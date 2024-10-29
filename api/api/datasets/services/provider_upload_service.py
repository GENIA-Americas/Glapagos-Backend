
import boto3
from botocore import UNSIGNED
from botocore.client import Config

from googleapiclient.discovery import build
from google.oauth2 import service_account

from api.datasets.exceptions import UrlFolderNameExtractionException


class ProviderService:
    @staticmethod
    def is_folder(url: str) -> bool:
        """
        Determines if a link contains a folder
        """
        ...

    @classmethod
    def list_files(cls, url: str) -> list:
        """List the files in a public folder"""
        ...


class GoogleDriveService(ProviderService):
    credentials = service_account.Credentials.from_service_account_file(
        "/app/config/drive_key.json",
        scopes=["https://www.googleapis.com/auth/drive"],
    )

    @staticmethod
    def is_folder(url: str) -> bool:
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
                fields="files(id, name, webViewLink, webContentLink, size)",
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
    def get_file_metadata(cls, url: str, fields: list[str]) -> dict:
        service = build("drive", "v3", credentials=cls.credentials)
        file_id = cls.get_file_id(url)

        meta = service.files().get(fileId=file_id, fields=",".join(fields)).execute()
        return meta

class S3Service(ProviderService):
    client = boto3.client("s3", config=Config(signature_version=UNSIGNED))

    @classmethod
    def is_folder(cls, url: str) -> bool:
        return True

    @classmethod
    def get_folder_name(cls, url: str) -> str:
        clean_url = url.replace("https://", "")
        folder_name = clean_url.split("/")[-2]

        if folder_name == "" or folder_name.find("/") != -1:
            raise UrlFolderNameExtractionException(error=f"Name extracted incorrectly: {folder_name}") 

        return folder_name + "/"
    
    @classmethod
    def get_bucket_name(cls, url: str) -> str:
        clean_url = url.replace("https://", "")
        bucket_name = clean_url.split(".")[0]

        return bucket_name
    
    @classmethod
    def get_file_name(cls, url: str) -> str:
        return ""

    @classmethod
    def list_files(cls, url: str) -> list:
        bucket_name = cls.get_bucket_name(url)
        folder_prefix = cls.get_folder_name(url)
        print("listing folder", bucket_name, folder_prefix)
        res = cls.client.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)

        if 'Contents' in res:
            print(res['Contents'])
        else:
            print("No objects found in this folder.")

        return res["Contents"]


