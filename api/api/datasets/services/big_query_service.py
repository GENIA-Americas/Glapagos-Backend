import json
import logging
from typing import List, Dict, Optional

from google.cloud import bigquery
from google.oauth2 import service_account
from google.api_core.exceptions import GoogleAPIError
from django.conf import settings

from api.datasets.exceptions import QueryFailedException, BigQueryMountTableException
from api.datasets.models import Table
from api.users.models import User

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {"csv", "json", "jsonl"}


class BigQueryService:
    def __init__(self, user: User, project_id: str = settings.BQ_PROJECT_ID) -> None:
        self.user: User = user
        self.project_id: str = project_id
        self.client = self.create_bigquery_client()

    def create_bigquery_client(self, project_owner: bool = False) -> bigquery.Client:
        if not self.user or project_owner:
            return bigquery.Client()

        account = self.user.service_account
        content = json.loads(account.key.private_key_data)
        credentials = service_account.Credentials.from_service_account_info(content)

        return bigquery.Client(credentials=credentials, location="US")

    @staticmethod
    def get_source_format(extension: str) -> bigquery.SourceFormat:
        """Returns the BigQuery SourceFormat based on file extension."""
        formats = {
            "csv": bigquery.SourceFormat.CSV,
            "json": bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
            "jsonl": bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        }
        ext = extension.lower()
        if ext not in formats:
            logger.warning("Unsupported extension '%s', defaulting to CSV format.", extension)
        return formats.get(ext, bigquery.SourceFormat.CSV)

    @classmethod
    def convert_schema_to_bigquery(cls, schema: List) -> List[bigquery.SchemaField]:
        bigquery_schema = []
        for field in schema:
            field_type = field["data_type"].upper()
            if field_type == "RECORD":
                nested = cls.convert_schema_to_bigquery(field.get("fields", []))
                schema_field = bigquery.SchemaField(
                    name=field["column_name"],
                    field_type=field_type,
                    mode=field.get("mode", "NULLABLE"),
                    fields=nested,
                )
            else:
                schema_field = bigquery.SchemaField(
                    name=field["column_name"],
                    field_type=field_type,
                    mode=field.get("mode", "NULLABLE"),
                )
            bigquery_schema.append(schema_field)
        return bigquery_schema

    def get_schema(self, dataset: str, table: str) -> List:
        query = (
            f"SELECT column_name, data_type, is_nullable "
            f"FROM `{self.project_id}.{dataset}.INFORMATION_SCHEMA.COLUMNS` "
            f"WHERE table_name = @table_name"
        )
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("table_name", "STRING", table)
            ]
        )
        schema = []
        try:
            rows = self.client.query(query, job_config=job_config).result()
            for field in rows:
                schema.append(
                    {
                        "column_name": field.column_name,
                        "data_type": field.data_type,
                        "mode": "NULLABLE" if field.is_nullable == "YES" else "REQUIRED",
                    }
                )
        except GoogleAPIError as exc:
            logger.error("Failed to fetch schema for %s.%s: %s", dataset, table, exc)
        return schema

    def get_dataset_reference(self, dataset: str) -> bigquery.DatasetReference:
        return bigquery.DatasetReference(self.project_id, dataset)

    def get_table_reference(self, dataset: str, table_name: str):
        dataset_ref = self.get_dataset_reference(dataset)
        bq_dataset = self.client.get_dataset(dataset_ref)
        return bq_dataset.table(table_name)

    def create_dataset(self, dataset_name: str):
        owner_client = self.create_bigquery_client(project_owner=True)
        dataset_ref = self.get_dataset_reference(dataset_name)
        return owner_client.create_dataset(dataset_ref)

    def query(
        self,
        query: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        job_config: Optional[bigquery.QueryJobConfig] = None,
    ):
        assert self.user, "User must be set to send a query"

        if limit is not None and offset is not None:
            if not (isinstance(limit, int) and isinstance(offset, int)):
                raise ValueError("limit and offset must be integers")

        try:
            job = self.client.query(query, job_config=job_config)
            result = job.result()

            if limit is not None and offset is not None:
                assert job.destination is not None, "Job destination should be defined"
                destination = self.client.get_table(job.destination)
                result = self.client.list_rows(
                    destination, start_index=offset, max_results=limit
                )

            return result
        except GoogleAPIError as exc:
            # Strip internal job ID / location info from the error message
            message = exc.message.split("\n")[0] if hasattr(exc, "message") else str(exc)
            logger.error("BigQuery query failed: %s", exc)
            raise QueryFailedException(detail=message, error=str(exc))

    def mount_table_from_gcs(
        self,
        table: Table,
        autodetect: bool,
        skip_leading_rows: int,
        schema: List,
        format_params: Optional[Dict] = None,
    ):
        try:
            owner_client = self.create_bigquery_client(project_owner=True)
            table_ref = self.get_table_reference(
                dataset=table.dataset_name, table_name=table.name
            )
            extension = table.file.type

            job_config = bigquery.LoadJobConfig(
                source_format=BigQueryService.get_source_format(extension),
                autodetect=autodetect,
            )

            if format_params:
                job_config.field_delimiter = format_params.get("delimiter", ",")
                job_config.quote_character = format_params.get("quotechar", '"')

            if skip_leading_rows:
                job_config.skip_leading_rows = skip_leading_rows

            if schema:
                job_config.schema = BigQueryService.convert_schema_to_bigquery(schema)
                job_config.autodetect = False  # explicit schema takes precedence

            load_job = owner_client.load_table_from_uri(
                table.file.storage_url, table_ref, job_config=job_config
            )
            load_job.result()
            table.update_table_stats(table_ref)

            if not table.schema:
                table.schema = self.get_schema(
                    dataset=table.dataset_name, table=table.name
                )
                table.save()

        except BigQueryMountTableException:
            raise
        except Exception as exc:
            logger.error("Failed to mount table from GCS: %s", exc, exc_info=True)
            raise BigQueryMountTableException(error=str(exc))
