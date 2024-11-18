from abc import ABC 
import requests

from django.utils.translation import gettext_lazy as _
from django.core.files.uploadedfile import TemporaryUploadedFile 

from api.datasets.enums import FileType
from api.datasets.exceptions import UploadFailedException, UrlFileNotExistException, UrlProviderException
from api.datasets.services.provider_upload_service import GoogleCloudService, GoogleDriveService, S3Service
from api.datasets.utils.json import get_content_from_url_json, prepare_json_data_format
from api.datasets.utils.csv import get_content_from_url_csv, prepare_csv_data_format
from api.datasets.utils.text import get_content_from_url_text 


def identify_url_provider(url: str) -> str:
    """
    Use to identify the different provider url if it can't
    assumes that the url is a file url
    """
    if url.find("drive.google.com") >= 0:
        return "google_drive"

    if url.find("amazonaws.com") >= 0 and url.find("s3") >= 0:
        return "s3"

    if url.find("storage.googleapis.com") >= 0:
        return "google_cloud"

    raise UrlProviderException(error=_("Provider in url not supported"))

def return_url_provider(url: str):
    """
    Returns an instance of the provider identified in the url
    """

    # Register here your file providers
    providers = dict(
        google_drive=GoogleDriveProvider(),
        s3=S3Provider(),
        google_cloud=GoogleCloudProvider()
    )

    provider = identify_url_provider(url)
    instance = providers.get(provider, None)

    if not instance:
        raise UrlProviderException(error=_("Provider not supported"))

    return instance 


class BaseUploadProvider(ABC):
    service: type 

    def process(self, url: str, skip_leading_rows: int, file_type: FileType) -> TemporaryUploadedFile:
        if self.service.is_folder(url):
            file = self.process_folder(url, skip_leading_rows, file_type)
        else:
            file = self.process_file(url, skip_leading_rows)
        return file

    def process_file(self, url: str, skip_leading_rows: int) -> TemporaryUploadedFile:
        r = requests.get(url, stream=True) 
        metadata = self.service.get_file_metadata(url)

        file = TemporaryUploadedFile(
            name=metadata.get("name"), 
            content_type='application/octet-stream', 
            size=metadata.get("size"),
            charset=None
        )

        if r.status_code == 200 and metadata.get("mimeType") in [
            "text/csv", "application/json", "text/plain"]:
            for chunk in r.iter_content(chunk_size=8192):
                file.write(chunk)
        else:
            raise UrlFileNotExistException()

        file.seek(0)
        return file

    def process_folder(
            self, 
            url: str, 
            skip_leading_rows: int, 
            file_type: FileType) -> TemporaryUploadedFile:

        files = self.service.list_files(url)
        size = 0
        for i in files:
            size += int(i.get("size", 0))

        file = TemporaryUploadedFile(
            name=files[0].get("name", ""), 
            content_type='application/octet-stream', 
            size=size,
            charset=None
        )

        urls = [i.get("webContentLink", "") for i in files]

        content = self.get_content_from_url(
            urls, 
            file_type, 
            max_lines=None, 
            skip_leading_rows=skip_leading_rows
        ) 
            
        file.write(content)
        file.seek(0)
        return file

    def preview(self, url: str, file_type: FileType) -> list:
        if self.service.is_folder(url):
            preview = self.preview_folder(url, file_type)
        else:
            preview = self.preview_file(url, file_type)
        return preview

    def preview_file(self, url: str, file_type: FileType) -> list:
        assert file_type not in FileType.choices, "file_type not supported"

        bigquery_format = list()
        preview = self.get_content_from_url([url], file_type, )
        bigquery_format = self.prepare_data_format(preview, file_type)

        return bigquery_format 
    
    def preview_folder(self, url: str, file_type: FileType) -> list:

        files = self.service.list_files(url)
        urls = [u.get("webContentLink", "") for u in files]

        bigquery_format = list()
        preview = self.get_content_from_url(urls, file_type, )
        bigquery_format = self.prepare_data_format(preview, file_type)

        return bigquery_format 

    def get_content_from_url(self, urls: list[str], file_type: FileType, **kwargs) -> str:
        assert file_type not in FileType.choices, "file_type not supported"

        content = ""
        if file_type == FileType.CSV: 
            content = get_content_from_url_csv(urls, skip_leading_rows=1, **kwargs)

        elif file_type == FileType.JSON:
            content = get_content_from_url_json(urls, **kwargs)

        elif file_type == FileType.TXT:
            content = get_content_from_url_text(urls, **kwargs)

        return content

    def prepare_data_format(self, data: str, file_type: FileType, **kwargs) -> list:
        assert file_type not in FileType.choices, "file_type not supported"

        bigquery_format = []
        if file_type == FileType.CSV: 
            bigquery_format = prepare_csv_data_format(data=data, skip_leading_rows=1)

        elif file_type == FileType.JSON:
            bigquery_format = prepare_json_data_format(data=data)

        elif file_type == FileType.TXT:
            raise UploadFailedException("txt format is not supported")

        return bigquery_format


class GoogleDriveProvider(BaseUploadProvider):
    service = GoogleDriveService

    def process_file(self, url: str, skip_leading_rows: int) -> TemporaryUploadedFile:
        d_url = self.service.convert_url(url)
        return super().process_file(d_url, skip_leading_rows)

    def preview_file(self, url: str, file_type: FileType) -> list:
        d_url = self.service.convert_url(url)
        return super().preview_file(url, file_type)


class S3Provider(BaseUploadProvider):
    service = S3Service 


class GoogleCloudProvider(BaseUploadProvider):
    service = GoogleCloudService 

