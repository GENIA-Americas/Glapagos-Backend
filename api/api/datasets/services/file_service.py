from abc import ABC, abstractmethod
from typing import List

from django.conf import settings

from api.users.models import User
from api.datasets.models import File, Table
from api.datasets.utils import (generate_random_string, csv_parameters_detect,
                                prepare_csv_data_format, prepare_json_data_format,
                                normalize_column_name)
from .big_query_service import BigQueryService
from .google_cloud_storage_service import GCSService, JSONGCSService


class FileServiceFactory:
    @staticmethod
    def get_file_service(user: User=None, return_instance=True, **kwargs):
        extension = kwargs['extension']
        class_ = None

        if extension.lower() == 'txt':
            class_ = TXTFileService
        elif extension.lower() == 'csv':
            class_ = CSVFileService
        elif extension.lower() == 'json':
            class_ = JSONFileService

        if not return_instance:
            return class_

        if class_:
            return class_(user, **kwargs)


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

    def __init__(self, user: User, **kwargs):
        super().__init__(user, **kwargs)
        self.autodetect = kwargs.get("autodetect", False)
        self.schema = kwargs.get("schema")

    def create_table_obj(self, file_obj: File) -> Table:
        dataset_name = settings.BQ_DATASET_ID
        if not self.public:
            dataset_name = self.user.service_account.dataset_name
        table = Table.objects.create(
            name=normalize_column_name(self.filename.split(".")[0]),
            dataset_name=dataset_name,
            file=file_obj,
            owner=file_obj.owner,
            public=self.public,
            schema=self.schema
        )
        table.save()
        return table

    @staticmethod
    @abstractmethod
    def preview(data: str, skip_leading_rows: int) -> List:
        ...

    @abstractmethod
    def process_file(self):
        ...


class TXTFileService(FileService):
    def process_file(self):
        file_url = GCSService.upload_file(self.file, self.filename)
        return file_url


class CSVFileService(StructuredFileService):
    def __init__(self, user: User, **kwargs):
        super().__init__(user, **kwargs)
        self.skip_leading_rows = kwargs.get("skip_leading_rows", 1)

    @staticmethod
    def preview(data: str, skip_leading_rows: int) -> List:
        return prepare_csv_data_format(data=data, skip_leading_rows=skip_leading_rows)

    def process_file(self):
        file_url = GCSService.upload_file(self.file, self.filename)
        file_obj = self.create_file_object(file_url)
        table_obj = self.create_table_obj(file_obj)
        sample = self.file.read(4096).decode("utf-8")
        self.file.seek(0)
        format_params = csv_parameters_detect(sample)

        big_query_service = BigQueryService(user=self.user)
        big_query_service.mount_table_from_gcs(
            table=table_obj,
            autodetect=self.autodetect,
            skip_leading_rows=self.skip_leading_rows,
            schema=self.schema,
            format_params=format_params
        )
        return file_url


class JSONFileService(StructuredFileService):

    @staticmethod
    def preview(data: str, skip_leading_rows: int) -> List:
        return prepare_json_data_format(data=data)

    def process_file(self):
        upload_service = JSONGCSService()
        file_url = upload_service.upload_file(self.file, self.filename)
        file_obj = self.create_file_object(file_url)
        table_obj = self.create_table_obj(file_obj)
        big_query_service = BigQueryService(user=self.user)
        big_query_service.mount_table_from_gcs(
            table=table_obj,
            autodetect=self.autodetect,
            skip_leading_rows=0,
            schema=self.schema
        )
        return file_url
