import json
from io import StringIO
from typing import List, Dict

# Google cloud
from google.oauth2 import service_account
from google.cloud import bigquery
from google.cloud import storage
from django.conf import settings

# Models
from api.datasets.models.service_account import ServiceAccount
from api.users.models import User
from api.datasets.models import Table


def search_query(user: User, query: str, job_config: bigquery.QueryJobConfig = None):
    account = ServiceAccount.objects.filter(owner=user).first()
    content = json.loads(account.key.private_key_data)
    credentials = service_account.Credentials.from_service_account_info(
        content
    )

    client = bigquery.Client(credentials=credentials, location="US")
    query_job = client.query(query, job_config=job_config)
    result = query_job.result()

    return result


def get_table_reference(project_id: str, dataset: str, table: str):
    client = bigquery.Client()
    dataset_ref = bigquery.DatasetReference(
        project_id, dataset
    )
    dataset = client.get_dataset(dataset_ref)
    table_ref = dataset.table(table)
    return table_ref


class GCSUploadServiceFactory:
    @staticmethod
    def get_upload_service(extension):
        if extension.lower() == "json":
            return JSONGCSUploadService()
        else:
            return GCSUploadService()


class GCSUploadService:

    def upload(self, file, filename: str) -> str:
        """Upload file to Google Cloud Storage."""
        client = storage.Client()
        bucket_name = settings.GCS_BUCKET
        bucket = client.get_bucket(bucket_name)
        blob = bucket.blob(filename)
        blob.upload_from_file(file, content_type=file.content_type)
        file.seek(0)
        return blob.public_url


class JSONGCSUploadService(GCSUploadService):

    def is_newline_delimited_json(self, content):
        try:
            for line in content.splitlines():
                json.loads(line)
            return True
        except json.JSONDecodeError:
            return False

    def convert_to_newline_delimited_json(self, file):
        content = file.read().decode("utf-8")

        if self.is_newline_delimited_json(content):
            return

        data = json.loads(content)
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            output = StringIO()
            for item in data:
                output.write(json.dumps(item) + "\n")
            output.seek(0)
            file.file = output
            file.size = len(output.getvalue())
            file.name = file.name

    def upload(self, file, filename: str) -> str:
        self.convert_to_newline_delimited_json(file)
        file.seek(0)
        return super().upload(file, filename)


class BigQueryLoadService:

    def get_source_format(self, extension: str):
        """Returns the BigQuery SourceFormat based on file extension."""
        formats = {
            "csv": bigquery.SourceFormat.CSV,
            "json": bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        }
        return formats.get(extension.lower(), bigquery.SourceFormat.CSV)

    def convert_schema_to_bigquery(self, schema: List):
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

    def mount_table(
        self,
        table: Table,
        autodetect,
        skip_leading_rows,
        schema: List,
        format_params: Dict,
    ):
        client = bigquery.Client()
        dataset_ref = bigquery.DatasetReference(
            settings.BQ_PROJECT_ID, table.dataset_name
        )
        dataset = client.get_dataset(dataset_ref)
        table_ref = dataset.table(table.name)
        extension = table.file.type

        job_config = bigquery.LoadJobConfig(
            source_format=self.get_source_format(extension),
            autodetect=autodetect,
            field_delimiter=format_params.get("delimiter", ","),
            quote_character=format_params.get("quotechar", '"'),
        )

        if skip_leading_rows:
            job_config.skip_leading_rows = skip_leading_rows
        if schema:
            schema = json.loads(schema[0])
            bigquery_schema = self.convert_schema_to_bigquery(schema)
            job_config.schema = bigquery_schema

        gcs_uri = table.file.storage_url

        load_job = client.load_table_from_uri(gcs_uri, table_ref, job_config=job_config)

        load_job.result()
        table.update_table_stats(table_ref)
