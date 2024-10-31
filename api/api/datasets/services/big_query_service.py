import json
from typing import List, Dict

from google.cloud import bigquery
from google.oauth2 import service_account
from google.api_core.exceptions import GoogleAPIError
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from api.datasets.exceptions import QueryFailedException, BigQueryMountTableException
from api.datasets.models import Table
from api.users.models import User


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
        }
        return formats.get(extension.lower(), bigquery.SourceFormat.CSV)

    @classmethod
    def convert_schema_to_bigquery(cls, schema: List) -> List[bigquery.SchemaField]:
        bigquery_schema = []

        for field in schema:
            if field["data_type"].upper() == "ARRAY":
                schema_field = bigquery.SchemaField(
                    name=field["column_name"],
                    field_type=field["data_type"],
                    mode=field.get("mode", "REPEATED"),
                )
            elif field["data_type"].upper() == "RECORD":
                fields_schema = cls.convert_schema_to_bigquery(field["fields"])
                schema_field = bigquery.SchemaField(
                    name=field["column_name"],
                    field_type=field["data_type"],
                    mode=field.get("mode", "REPEATED"),
                    fields=fields_schema
                )
            else:
                schema_field = bigquery.SchemaField(
                    name=field["column_name"],
                    field_type=field["data_type"],
                    mode=field.get("mode", "REPEATED"),
                )
            bigquery_schema.append(schema_field)
        return bigquery_schema

    def get_schema(self, dataset: str, table: str) -> List:
        query = f"""SELECT column_name, data_type, is_nullable 
                    FROM `{self.project_id}.{dataset}.INFORMATION_SCHEMA.COLUMNS` 
                    WHERE table_name = '{table}';"""
        schema = []
        try:
            bigquery_schema = self.query(query)
            if not bigquery_schema:
                return schema
            for field in bigquery_schema:
                schema.append({
                    "column_name": field.column_name,
                    "data_type": field.data_type,
                    "mode": "NULLABLE" if field.is_nullable else "REQUIRED",
                })
        except GoogleAPIError as exp:
            print(str(exp))
        return schema

    def get_dataset_reference(self, dataset: str) -> bigquery.DatasetReference:
        dataset_ref = bigquery.DatasetReference(
            self.project_id, dataset
        )
        return dataset_ref

    def get_table_reference(self, dataset: str, table_name: str):
        dataset_ref = self.get_dataset_reference(dataset)
        dataset = self.client.get_dataset(dataset_ref)
        table_ref = dataset.table(table_name)
        return table_ref

    def create_dataset(self, dataset_name: str):
        owner_client = self.create_bigquery_client(project_owner=True)
        dataset_ref = self.get_dataset_reference(dataset_name)
        dataset = owner_client.create_dataset(dataset_ref)
        return dataset

    def query(self, query: str, limit: int | None = None, offset: int | None = None,
              job_config: bigquery.QueryJobConfig = None):
        assert self.user, "User must be set to send a query"
        try:
            job = self.client.query(query, job_config=job_config)
            result = job.result()

            if limit is not None and offset is not None:
                assert (
                        type(offset) is int and type(limit) is int
                ), "limit and offset must be integers"

                assert job.destination is not None, "Job destination should be defined"

                destination = self.client.get_table(job.destination)
                result = self.client.list_rows(destination, start_index=offset, max_results=limit)

            return result
        except GoogleAPIError as exp:
            # remove the job id and location
            message = exp.message.split("\n")[0]
            raise QueryFailedException(
                detail=message,
                error=str(exp)
            )

    def mount_table_from_gcs(
            self,
            table: Table,
            autodetect: bool,
            skip_leading_rows: int,
            schema: List,
            format_params: Dict = None,
    ):
        try:
            owner_client = self.create_bigquery_client(project_owner=True)
            table_ref = self.get_table_reference(dataset=table.dataset_name, table_name=table.name)
            extension = table.file.type

            job_config = bigquery.LoadJobConfig(
                source_format=BigQueryService.get_source_format(extension),
                autodetect=autodetect,
            )

            if format_params:
                job_config.field_delimiter = format_params.get("delimiter", ",")
                job_config.quote_character = format_params.get("quotechar", ",")

            if skip_leading_rows:
                job_config.skip_leading_rows = skip_leading_rows
            if schema:
                bigquery_schema = BigQueryService.convert_schema_to_bigquery(schema)
                job_config.schema = bigquery_schema

            gcs_uri = table.file.storage_url
            load_job = owner_client.load_table_from_uri(gcs_uri, table_ref, job_config=job_config)

            load_job.result()
            table.update_table_stats(table_ref)
            if not table.schema:
                table.schema = self.get_schema(dataset=table.dataset_name, table=table.name)
                table.save()
        except Exception as exp:
            raise exp
            raise BigQueryMountTableException(error=str(exp))
