import json
from abc import ABC, abstractmethod
from io import StringIO
from typing import List

from django.conf import settings
from google.cloud import storage
from google.cloud import bigquery

from api.users.models import User
from api.datasets.models import File, Table
from api.datasets.utils import generate_random_string


class GCSUploadServiceFactory:
    @staticmethod
    def get_upload_service(extension):
        if extension.lower() == 'json':
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
        content = file.read().decode('utf-8')

        if self.is_newline_delimited_json(content):
            return

        data = json.loads(content)
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            output = StringIO()
            for item in data:
                output.write(json.dumps(item) + '\n')
            output.seek(0)
            file.file = output
            file.size = len(output.getvalue())
            file.name = file.name

    def upload(self, file, filename: str) -> str:
        self.convert_to_newline_delimited_json(file)
        file.seek(0)
        return super().upload(file, filename)


class BigQueryLoadService:

    def update_table_info(self, table_ref, table_obj: Table):
        client = bigquery.Client()
        table_bq = client.get_table(table_ref)
        table_obj.mounted = True
        table_obj.data_expiration = table_bq.expires
        table_obj.number_of_rows = table_bq.num_rows
        table_obj.total_logical_bytes = table_bq.num_bytes
        table_obj.save()

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
                    name=field['column_name'],
                    field_type=field['data_type'],
                    mode=field.get('mode', 'NULLABLE')
                )
            )
        return bigquery_schema

    def mount_table(self, table: Table, autodetect, skip_leading_rows, schema: List):
        client = bigquery.Client()
        dataset_ref = bigquery.DatasetReference(settings.BQ_PROJECT_ID, table.dataset_name)
        dataset = client.get_dataset(dataset_ref)
        table_ref = dataset.table(table.name)
        extension = table.file.type

        job_config = bigquery.LoadJobConfig(
            source_format=self.get_source_format(extension),
            autodetect=autodetect,
        )

        if skip_leading_rows:
            job_config.skip_leading_rows = skip_leading_rows
        if schema:
            schema = json.loads(schema[0])
            bigquery_schema = self.convert_schema_to_bigquery(schema)
            job_config.schema = bigquery_schema

        gcs_uri = table.file.storage_url

        load_job = client.load_table_from_uri(
            gcs_uri, table_ref, job_config=job_config
        )

        load_job.result()
        self.update_table_info(table_ref, table)


class FileServiceFactory:
    @staticmethod
    def get_file_service(user: User, **kwargs):
        extension = kwargs['extension']

        if extension.lower() == 'txt':
            return TXTFileService(user, **kwargs)
        elif extension.lower() == 'csv':
            return CSVFileService(user, **kwargs)
        elif extension.lower() == 'json':
            return JSONFileService(user, **kwargs)


class FileService(ABC):
    def __init__(self, user: User = None, **kwargs):
        self.file = kwargs["file"]
        self.extension = kwargs["extension"]
        self.public = kwargs["public"]
        self.user = user
        self.filename = f"{generate_random_string(10)}_{kwargs['file'].name}"

    def create_file_object(self, file_url: str):
        file_obj = File.objects.create(
            name=self.filename,
            type=self.extension,
            storage_url=file_url,
            public=self.public,
            owner=self.user
        )
        file_obj.save()
        return file_obj

    @abstractmethod
    def process_file(self):
        ...


class StructuredFileService(FileService):

    def create_table_obj(self, file_obj: File) -> Table:
        table = Table.objects.create(
            name=self.filename.split(".")[0],
            dataset_name=settings.BQ_DATASET_ID,
            file=file_obj
        )
        table.save()
        return table

    @abstractmethod
    def process_file(self):
        ...


class TXTFileService(FileService):
    def process_file(self):
        upload_service = GCSUploadService()
        file_url = upload_service.upload(self.file, self.filename)
        return file_url


class CSVFileService(StructuredFileService):
    def __init__(self, user: User, **kwargs):
        super().__init__(user, **kwargs)
        self.skip_leading_rows = kwargs.get("skip_leading_rows", 1)
        self.autodetect = kwargs.get("autodetect", False)
        self.schema = kwargs.get("schema")

    def process_file(self):
        upload_service = GCSUploadService()
        file_url = upload_service.upload(self.file, self.filename)
        file_obj = self.create_file_object(file_url)
        table_obj = self.create_table_obj(file_obj)
        big_query_service = BigQueryLoadService()
        big_query_service.mount_table(
            table=table_obj,
            autodetect=self.autodetect,
            skip_leading_rows=self.skip_leading_rows,
            schema=self.schema
        )
        return file_url


class JSONFileService(StructuredFileService):
    def process_file(self):
        upload_service = JSONGCSUploadService()
        file_url = upload_service.upload(self.file, self.filename)
        file_obj = self.create_file_object(file_url)
        table_obj = self.create_table_obj(file_obj)
        big_query_service = BigQueryLoadService()
        big_query_service.mount_table(table=table_obj, autodetect=True, skip_leading_rows=0, schema=[])
        return file_url
