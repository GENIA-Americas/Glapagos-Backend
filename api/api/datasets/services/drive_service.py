from abc import ABC, abstractmethod
from googleapiclient.discovery import build
from google.oauth2 import service_account

from api.datasets.exceptions import UrlFolderNameExtractionException


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


class GoogleDriveService(ProviderService):
    credentials = service_account.Credentials.from_service_account_file(
        "/app/config/drive_key.json",
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
    def get_file_metadata(cls, url: str, fields: list[str]) -> dict:
        service = build("drive", "v3", credentials=cls.credentials)
        file_id = cls.get_file_id(url)

        meta = service.files().get(fileId=file_id, fields=",".join(fields)).execute()
        return meta
