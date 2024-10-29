from abc import ABC, abstractmethod
import requests

from django.utils.translation import gettext_lazy as _
from django.core.files.uploadedfile import TemporaryUploadedFile 

from api.datasets.exceptions import UrlFileNotExistException, UrlProviderException
from api.datasets.services.drive_service import GoogleDriveService
from api.datasets.utils.csv import get_preview_from_url_csv


def identify_url_provider(url: str) -> str:
    """
    Use to identify the different provider url if it can't
    assumes that the url is a file url
    """
    if url.find("drive.google.com") >= 0:
        return "google_drive"

    return "file"

def return_url_provider(url: str):
    """
    Returns an instance of the provider identified in the url
    """

    # Register here your file providers
    providers = dict(
        google_drive=GoogleDriveProvider(url)
    )

    try:
        instance = providers[identify_url_provider(url)]
    except Exception as e:
        raise UrlProviderException(error=e)

    return instance 


class BaseUploadProvider(ABC):
    service: type 
    preview_content: str
    extension: str

    def __init__(self, url: str):
        self.url = url

    def process(self, skip_leading_rows: int) -> TemporaryUploadedFile:
        if self.service.is_folder(self.url):
            file = self.process_folder(skip_leading_rows)
        else:
            file = self.process_file(skip_leading_rows)
        return file

    @abstractmethod
    def process_file(self, skip_leading_rows: int) -> TemporaryUploadedFile:
        ...

    @abstractmethod
    def process_folder(self, skip_leading_rows: int) -> TemporaryUploadedFile:
        ...

    def preview(self) -> str:
        if self.service.is_folder(self.url):
            preview = self.preview_folder()
        else:
            preview = self.preview_file()
        return preview

    @abstractmethod
    def preview_file(self) -> str:
        ...
    
    @abstractmethod
    def preview_folder(self) -> str:
        ...

class GoogleDriveProvider(BaseUploadProvider):
    service = GoogleDriveService

    def process_file(self, skip_leading_rows: int) -> TemporaryUploadedFile:
        d_url = self.service.convert_url(self.url)
        r = requests.get(d_url, stream=True) 
        metadata = self.service.get_file_metadata(self.url, ["name", "size", "mimeType"])

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


    def process_folder(self, skip_leading_rows: int) -> TemporaryUploadedFile:
        files = self.service.list_files(self.url)
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

    def preview_folder(self) -> str:
        files = self.service.list_files(self.url)
        urls = [u.get("webContentLink", "") for u in files]
        preview = get_preview_from_url_csv(urls)

        self.preview_content = preview.getvalue()
        return self.preview_content

    def preview_file(self) -> str:
        d_url = self.service.convert_url(self.url)
        self.preview_content = get_preview_from_url_csv([d_url]).getvalue()
        return self.preview_content


