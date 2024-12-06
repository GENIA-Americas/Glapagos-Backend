import json
from io import StringIO

from google.cloud import storage
from django.conf import settings

from api.datasets.exceptions import UploadFailedException, CloudStorageOperationException


class GCSService:

    @classmethod
    def upload_file(cls, file, filename: str) -> str:
        """Upload file to Google Cloud Storage."""
        try:
            client = storage.Client()
            bucket_name = settings.GCS_BUCKET
            bucket = client.get_bucket(bucket_name)
            blob = bucket.blob(filename)
            blob.upload_from_file(file, content_type=file.content_type)
            file.seek(0)
            return blob.public_url
        except Exception as exp:
            raise UploadFailedException(error=str(exp))

    @staticmethod
    def create_folder(bucket_name: str, folder_name: str) -> None:
        """Create a folder in Google Cloud Storage."""
        try:
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)

            blobs = list(storage_client.list_blobs(bucket, prefix=f"{folder_name}/", max_results=1))
            if blobs:
                return

            blob = bucket.blob(f"{folder_name}/")
            blob.upload_from_string("")
        except Exception as exp:
            raise CloudStorageOperationException(error=str(exp))


class JSONGCSService(GCSService):

    @staticmethod
    def is_newline_delimited_json(content: str) -> bool:
        try:
            lines = content.splitlines()
            if len(lines) <= 1:
                return False
            for line in lines:
                line = line.strip()
                if line:
                    json.loads(line)
            return True
        except json.JSONDecodeError:
            return False

    @classmethod
    def convert_to_newline_delimited_json(cls, file) -> None:
        content = file.read().decode("utf-8")
        if cls.is_newline_delimited_json(content):
            return
        data = json.loads(content)
        output = StringIO()
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            for item in data:
                output.write(json.dumps(item) + "\n")

        elif isinstance(data, dict):
            output.write(json.dumps(data))

        else:
            return None

        output.seek(0)
        file.file = output
        file.size = len(output.getvalue())
        file.name = file.name

    @classmethod
    def upload_file(cls, file, filename: str) -> str:
        cls.convert_to_newline_delimited_json(file)
        file.seek(0)
        return super(JSONGCSService, cls).upload_file(file, filename)


class GCSUploadFactory:
    @staticmethod
    def get_upload_service(extension) -> type(GCSService):
        if extension.lower() == "json":
            return JSONGCSService
        else:
            return GCSService
