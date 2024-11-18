
from abc import ABC, abstractmethod

import boto3
from botocore import UNSIGNED
from botocore.client import Config
from django.conf import settings
from googleapiclient.discovery import build
from google.oauth2 import service_account

from django.utils.translation import gettext_lazy as _
from api.datasets.exceptions import UrlFolderNameExtractionException, UrlProviderException


class ProviderService(ABC):
    @classmethod
    @abstractmethod
    def is_folder(cls, url: str) -> bool:
        """
        Determines if a link contains a folder
        """
        ...

    @classmethod
    @abstractmethod
    def list_files(cls, url: str) -> list:
        """List the files in a public folder"""
        ...

    @classmethod
    @abstractmethod
    def get_file_metadata(cls, url: str) -> dict:
        """Gets the file metadata"""
        ...

class GoogleDriveService(ProviderService):
    credentials = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_DRIVE_KEY,
        scopes=["https://www.googleapis.com/auth/drive"],
    )

    @classmethod
    def is_folder(cls, url: str) -> bool:
        """
        Determines if a link contains a folder
        """

        if url.find("https://drive.google.com/drive/folders/") >= 0:
            return True 

        return False 

    @classmethod
    def get_folder_name(cls, url: str) -> str:
        """
        Extracts the name of the folder from the given url
        """

        clean_url = url.replace("https://drive.google.com/drive/folders/", "")
        folder_name = clean_url.split("?")[0]

        if folder_name == "" or folder_name.find("/") != -1:
            raise UrlFolderNameExtractionException(error=f"Name extracted incorrectly: {folder_name}") 

        return folder_name

    @classmethod
    def get_file_id(cls, url: str) -> str:
        """
        Extracts the file id form the given url
        """
        clean_url = url.replace("https://drive.google.com/file/d/", "")
        file_id = clean_url.split("/")[0]
        return file_id
        
    @classmethod
    def list_files(cls, url: str) -> list:
        """List the files in a public folder"""

        service = build("drive", "v3", credentials=cls.credentials)

        folder_name = cls.get_folder_name(url)
        results = (
            service.files()
            .list(
                q=f"'{folder_name}' in parents and trashed=false",
                fields="files(id, name, webViewLink, webContentLink, size, mimeType)",
            )
            .execute()
        )
        files = results.get("files", [])

        return files
    
    @classmethod
    def convert_url(cls, url: str):
        """
        Converts the native sharing url from google drive
        to a downloadable content link
        """
        file_id = cls.get_file_id(url)
        return f"https://drive.google.com/uc?export=download&id={file_id}"

    @classmethod
    def get_file_metadata(cls, url: str) -> dict:
        service = build("drive", "v3", credentials=cls.credentials)
        file_id = cls.get_file_id(url)

        meta = service.files().get(fileId=file_id, fields="name, size, mimeType").execute()
        return meta

class S3Service(ProviderService):
    client = boto3.client("s3", config=Config(signature_version=UNSIGNED))

    @classmethod
    def is_folder(cls, url: str) -> bool:
        """
        Determines if a link contains a folder
        """
        url_clean = url.split("/")[-1]
        if url_clean != "":
            return False

        return True

    @classmethod
    def is_file(cls, url: str) -> bool:
        """
        Determines if a link contains a file 
        """
        url_clean = url.split("/")[-1]
        if url_clean == "":
            return False

        return True

    @classmethod
    def is_presign_url(cls, url: str) -> bool:
        """
        Determines if a link is a presign url by counting the
        number of amazon headers that it has
        """
        count = url.count("X-Amz")
        if count != 8 :
            return False

        return True

    @classmethod
    def get_folder_name(cls, url: str) -> str:
        clean_url = url.replace("https://", "")
        folder_name = clean_url.split("/")[-2]

        if folder_name == "" or folder_name.find("/") != -1:
            raise UrlFolderNameExtractionException(error=f"Name extracted incorrectly: {folder_name}") 

        return folder_name + "/"

    @classmethod
    def get_file_name(cls, url: str) -> str:
        clean_url = url.replace("https://", "")
        name = clean_url.split("?")[0].split("/")[-1]

        if name == "" :
            raise UrlFolderNameExtractionException(error=f"Name extracted incorrectly: {name}") 

        return name 

    @classmethod
    def get_object_key(cls, url: str) -> str:
        object_key = url.split("amazonaws.com/")[-1]
        if "?" in object_key:
            object_key = object_key.split("?")[0]

        if object_key == "":
            raise UrlFolderNameExtractionException(error=f"Object key extracted incorrectly: {object_key}") 

        return object_key 
    
    @classmethod
    def get_bucket_name(cls, url: str) -> str:
        clean_url = url.replace("https://", "")
        bucket_name = clean_url.split(".")[0]

        return bucket_name
    
    @classmethod
    def list_files(cls, url: str) -> list:
        bucket_name = cls.get_bucket_name(url)
        folder_prefix = cls.get_folder_name(url)

        res = dict() 
        try:
            res = cls.client.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)
        except Exception as e:
            raise UrlFolderNameExtractionException(
                _("Access denied when requesting resources, check your bucket permissions"))

        if 'Contents' not in res:
            raise UrlFolderNameExtractionException(_("No objects found in this folder"))

        items = []
        for i in res["Contents"]:
            object_key = i.get("Key")
            head_res = cls.client.head_object(Bucket=bucket_name, Key=object_key)
            content_type = head_res.get("ContentType", "application/octet-stream")

            name =i.get("Key").split("/")[-1]
            if name: # removes the directory element
                items.append(
                    dict(
                        name=name,
                        size=i.get("Size"),
                        mimeType=content_type,
                        webContentLink=f"{url}{name}"
                    )
                ) 

        return items 

    @classmethod
    def get_file_metadata(cls, url: str) -> dict:
        bucket_name = cls.get_bucket_name(url)
        object_key = cls.get_object_key(url) 

        try:
            res = cls.client.head_object(Bucket=bucket_name, Key=object_key)
        except Exception as e:
            raise UrlProviderException(
                _("Invalid or forbidden url, check that your bucket has the correct permissions")
            )

        content_type = res.get("ContentType", "application/octet-stream")
        size = res.get("ContentLength", 0)

        item = dict(
            name=object_key.split("/")[-1],
            size=size,
            mimeType=content_type
        )

        return item 
 
