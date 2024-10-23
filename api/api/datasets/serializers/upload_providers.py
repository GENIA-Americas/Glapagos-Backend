import io
import requests

from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.core.files.uploadedfile import TemporaryUploadedFile 

from api.datasets.services.drive_service import GoogleDriveService
from api.datasets.utils.csv import get_preview_from_url_csv
from api.datasets.serializers.file import UrlPreviewSerializer
from api.datasets.enums import FileType


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
    Returns an instance of the provider indentified in the url
    """

    # Register here your file providers
    providers = dict(
        google_drive=GoogleDriveProvider()
    )

    try:
        instance = providers[identify_url_provider(url)]
    except Exception as e:
        raise serializers.ValidationError(
            _("Couln't identify provider in url, or maybe is not register in providers")
        ) 

    return instance 


class BaseUploadProvider():
    serializer = UrlPreviewSerializer 
    service: type 
    files: list
    preview_content: str
    extension: str
    url: str

    def process(self) -> TemporaryUploadedFile:
        ...

    def process_file(self) -> TemporaryUploadedFile:
        ...

    def process_folder(self) -> TemporaryUploadedFile:
        ...

    def validate(self, data):
        ...

    def validate_folder(self):
        ...

    def validate_file(self):
        ...

    def preview(self) -> str:
        ...

    def preview_file(self) -> str:
        ...
    
    def preview_folder(self) -> str:
        ...

class GoogleDriveProvider(BaseUploadProvider):
    service = GoogleDriveService

    def process(self):
        if self.service.is_folder(self.url):
            file = self.process_folder()
        else:
            file = self.process_file()
        return file

    def process_file(self):
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
            raise serializers.ValidationError(
                {"detail": _("Invalid url or file doesn't exist")},
            )

        file.seek(0)
        return file

    def process_folder(self):

        size = 0
        for i in self.files:
            size += int(i.get("size", 0))

        file = TemporaryUploadedFile(
            name=self.files[0].get("name", ""), 
            content_type='application/octet-stream', 
            size=size,
            charset=None
        )

        column = False 
        for i in self.files:
            url = i.get("webContentLink", "")
            f = requests.get(url, stream=True)

            line = 0
            for j in f.iter_lines():
                if line != 0 or not column:
                    column = True
                    file.write(j + "\r\n".encode("utf-8"))
                line += 1
            
        file.seek(0)
        return file

    def preview(self):
        if self.service.is_folder(self.url):
            preview = self.preview_folder()
        else:
            preview = self.preview_file()
        return preview

    def preview_folder(self) -> str:
        urls = [u.get("webContentLink", "") for u in self.files]
        preview = get_preview_from_url_csv(urls)

        self.preview_content = preview.getvalue()
        return self.preview_content

    def preview_file(self) -> str:
        d_url = self.service.convert_url(self.url)
        self.preview_content = get_preview_from_url_csv([d_url]).getvalue()
        return self.preview_content

    def validate_folder(self):
        files = self.service.list_files(self.url)
        self.files = files

        extension = ""
        for i in files:
            name = i.get("name", "").split(".")[-1]
            if not name in FileType.values:
                raise serializers.ValidationError(dict(detail=(f"{name} {_('is not a valid file extension')}")))

            if extension == "":
                extension = name

            if extension != name:
                raise serializers.ValidationError(
                    dict(detail=_("Invalid extension, all files should have the same file extension"))
                )
        self.extension = extension

        size = 0
        for i in self.files:
            size += int(i.get("size", 0))

        # limit to 100MB
        if size >= 100_000_000: 
            raise serializers.ValidationError(
                dict(detail=_("The files size are too large"))
            )


    def validate_file(self):
        metadata = self.service.get_file_metadata(self.url, ["size", "name"])
        size = int(metadata.get("size", 0))

        extension = metadata.get("name", "").split(".")[-1]
        if not extension in FileType.values:
            raise serializers.ValidationError(dict(detail=(f"{extension} {_('is not a valid file extension')}")))

        # limit to 100MB
        if size >= 100_000_000: 
            raise serializers.ValidationError(
                dict(detail=_("The file size is too large"))
            )


    def validate(self, data):
        serializer = self.serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.url = serializer.validated_data.get("url", "")

        if self.service.is_folder(self.url):
            self.validate_folder()
        else:
            self.validate_file()

