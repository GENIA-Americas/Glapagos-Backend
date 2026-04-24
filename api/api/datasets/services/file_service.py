import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional

from django.conf import settings

from api.users.models import User
from api.datasets.models import File, Table
from api.datasets.utils import (
    csv_parameters_detect,
    prepare_csv_data_format,
    prepare_json_data_format,
    normalize_column_name,
)
from api.utils.basics import generate_random_string
from .big_query_service import BigQueryService
from .google_cloud_storage_service import GCSService, JSONGCSService

logger = logging.getLogger(__name__)


class FileServiceFactory:
    _EXTENSION_MAP = {
        "txt": "TXTFileService",
        "csv": "CSVFileService",
        "json": "JSONFileService",
        "jsonl": "JSONFileService",
    }

    @staticmethod
    def get_file_service(
        user: Optional[User] = None, return_instance: bool = True, **kwargs
    ):
        extension = kwargs.get("extension", "").lower()
        class_name = FileServiceFactory._EXTENSION_MAP.get(extension)
        if not class_name:
            logger.warning("Unsupported file extension: %s", extension)
            return None

        cls = globals().get(class_name)
        if cls is None:
            return None

        return cls(user, **kwargs) if return_instance else cls


class FileService(ABC):
    def __init__(self, user: Optional[User] = None, **kwargs):
        self.file = kwargs["file"]
        self.extension = kwargs["extension"].lower()
        self.public = kwargs["public"]
        self.user = user
        self.description = kwargs.get("description", "")

        base, ext = os.path.splitext(kwargs["file"].name)
        safe_name = normalize_column_name(base)
        rand = generate_random_string(10)
        self.filename = f"{rand}_{safe_name}{ext}"

    def create_file_object(self, file_url: str) -> File:
        return File.objects.create(
            name=self.filename,
            type=self.extension,
            storage_url=file_url,
            public=self.public,
            owner=self.user,
            description=self.description,
        )

    @abstractmethod
    def process_file(self):
        ...


class StructuredFileService(FileService):
    def __init__(self, user: Optional[User], **kwargs):
        super().__init__(user, **kwargs)
        self.autodetect: bool = kwargs.get("autodetect", False)
        self.schema: Optional[List] = kwargs.get("schema")

    def create_table_obj(self, file_obj: File) -> Table:
        if self.public:
            dataset_name = settings.BQ_DATASET_ID
        else:
            dataset_name = self.user.service_account.dataset_name

        return Table.objects.create(
            name=self.filename.rsplit(".", 1)[0],
            dataset_name=dataset_name,
            file=file_obj,
            owner=file_obj.owner,
            public=self.public,
            schema=self.schema,
            description=file_obj.description,
        )

    @staticmethod
    @abstractmethod
    def preview(data: str, skip_leading_rows: int) -> List:
        ...

    @abstractmethod
    def process_file(self):
        ...


class TXTFileService(FileService):
    def process_file(self):
        return GCSService.upload_file(self.file, self.filename)


class CSVFileService(StructuredFileService):
    def __init__(self, user: Optional[User], **kwargs):
        super().__init__(user, **kwargs)
        self.skip_leading_rows: int = kwargs.get("skip_leading_rows", 1)

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

        bq = BigQueryService(user=self.user)
        bq.mount_table_from_gcs(
            table=table_obj,
            autodetect=self.autodetect,
            skip_leading_rows=self.skip_leading_rows,
            schema=self.schema,
            format_params=format_params,
        )
        logger.info("CSV file uploaded and mounted: %s", self.filename)
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

        bq = BigQueryService(user=self.user)
        bq.mount_table_from_gcs(
            table=table_obj,
            autodetect=self.autodetect,
            skip_leading_rows=0,
            schema=self.schema,
        )
        logger.info("JSON file uploaded and mounted: %s", self.filename)
        return file_url
