import json
from typing import List, Dict

from google.cloud import bigquery
from google.oauth2 import service_account
from django.conf import settings

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

    @staticmethod
    def convert_schema_to_bigquery(schema: List) -> List[bigquery.SchemaField]:
        bigquery_schema = []

        for field in schema:
            bigquery_schema.append(
                bigquery.SchemaField(
                    name=field["column_name"],
                    field_type=field["data_type"],
                    mode=field.get("mode", "NULLABLE"),
                )
            )
        return bigquery_schema

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

    def create_empty_table(self, table: Table):
        table_ref = self.get_table_reference(dataset=table.dataset_name, table_name=table.name)
        empty_table = bigquery.Table(table_ref)
        empty_table = self.client.create_table(empty_table)
        print(f"Table {empty_table.project}.{empty_table.dataset_id}.{empty_table.table_id} created without schema.")
        table.mounted = True
        table.save()

    def create_dataset(self, dataset_name: str):
        owner_client = self.create_bigquery_client(project_owner=True)
        dataset_ref = self.get_dataset_reference(dataset_name)
        dataset = owner_client.create_dataset(dataset_ref)
        return dataset

    def query(self, query: str, limit: int | None = None, offset: int | None = None,
              job_config: bigquery.QueryJobConfig = None):
        assert self.user, "User must be set to send a query"
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

    def mount_table_from_gcs(
            self,
            table: Table,
            autodetect,
            skip_leading_rows,
            schema: List,
            format_params: Dict,
    ):
        owner_client = self.create_bigquery_client(project_owner=True)
        table_ref = self.get_table_reference(dataset=table.dataset_name, table_name=table.name)
        extension = table.file.type

        job_config = bigquery.LoadJobConfig(
            source_format=BigQueryService.get_source_format(extension),
            autodetect=autodetect,
            field_delimiter=format_params.get("delimiter", ","),
            quote_character=format_params.get("quotechar", '"'),
        )

        if skip_leading_rows:
            job_config.skip_leading_rows = skip_leading_rows
        if schema:
            schema = json.loads(schema[0])
            bigquery_schema = BigQueryService.convert_schema_to_bigquery(schema)
            job_config.schema = bigquery_schema

        gcs_uri = table.file.storage_url
        load_job = owner_client.load_table_from_uri(gcs_uri, table_ref, job_config=job_config)

        load_job.result()
        table.update_table_stats(table_ref)
