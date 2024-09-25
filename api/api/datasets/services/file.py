from abc import ABC, abstractmethod

from django.conf import settings

from api.users.models import User
from api.datasets.models import File, Table
from api.datasets.utils import generate_random_string, csv_parameters_detect
from api.datasets.services.google_cloud_services import (
    GCSUploadService,
    JSONGCSUploadService,
    BigQueryLoadService
)


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
        sample = self.file.read(4096).decode("utf-8")
        self.file.seek(0)
        format_params = csv_parameters_detect(sample)

        big_query_service = BigQueryLoadService()
        big_query_service.mount_table(
            table=table_obj,
            autodetect=self.autodetect,
            skip_leading_rows=self.skip_leading_rows,
            schema=self.schema,
            format_params=format_params
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
