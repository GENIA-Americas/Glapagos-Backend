from abc import ABC, abstractmethod
import requests

from django.utils.translation import gettext_lazy as _
from django.core.files.uploadedfile import TemporaryUploadedFile 

from api.datasets.exceptions import UrlFileNotExistException, UrlProviderException
from api.datasets.services.provider_upload_service import GoogleCloudService, GoogleDriveService, S3Service
from api.datasets.utils.csv import get_preview_from_url_csv


def identify_url_provider(url: str) -> str:
    """
    Use to identify the different provider url if it can't
    assumes that the url is a file url
    """
    if url.find("drive.google.com") >= 0:
        return "google_drive"

    if url.find("amazonaws.com") >= 0 and url.find("s3") >= 0:
        return "s3"

    if url.find("storage.googleapis.com") >= 0 or url.find("storage.cloud.google.com") >= 0:
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

    def process(self, url, skip_leading_rows: int) -> TemporaryUploadedFile:
        if self.service.is_folder(url):
            file = self.process_folder(url, skip_leading_rows)
        else:
            file = self.process_file(url, skip_leading_rows)
        return file

    def process_file(self, url, skip_leading_rows: int) -> TemporaryUploadedFile:
        r = requests.get(url, stream=True) 
        metadata = self.service.get_file_metadata(url)

        file = TemporaryUploadedFile(
            name=metadata.get("name"), 
            content_type='application/octet-stream', 
            size=metadata.get("size"),
            charset=None
        )

        if r.status_code == 200:
            for chunk in r.iter_content(chunk_size=8192):
                file.write(chunk)
        else:
            raise UrlFileNotExistException()

        file.seek(0)
        return file

    def process_folder(self, url, skip_leading_rows: int) -> TemporaryUploadedFile:
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

        column = False 
        for i in files:
            url = i.get("webContentLink", "")
            f = requests.get(url, stream=True)

            line = 0
            for j in f.iter_lines():
                if line not in range(skip_leading_rows) or not column:
                    column = True
                    file.write(j + "\r\n".encode("utf-8"))
                line += 1
            
        file.seek(0)
        return file

    def preview(self, url) -> str:
        if self.service.is_folder(url):
            preview = self.preview_folder(url)
        else:
            preview = self.preview_file(url)
        return preview

    def preview_file(self, url) -> str:
        preview = get_preview_from_url_csv([url]).getvalue()
        return preview 
    
    def preview_folder(self, url) -> str:
        files = self.service.list_files(url)
        urls = [u.get("webContentLink", "") for u in files]
        preview = get_preview_from_url_csv(urls)

        return preview.getvalue() 


class GoogleDriveProvider(BaseUploadProvider):
    service = GoogleDriveService

    def process_file(self, url, skip_leading_rows: int) -> TemporaryUploadedFile:
        d_url = self.service.convert_url(url)
        return super().process_file(d_url, skip_leading_rows)

    def preview_file(self, url) -> str:
        d_url = self.service.convert_url(url)
        return super().preview_file(d_url) 


class S3Provider(BaseUploadProvider):
    service = S3Service 


class GoogleCloudProvider(BaseUploadProvider):
    service = GoogleCloudService 

