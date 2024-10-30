import json
from io import StringIO

from google.cloud import storage
from django.conf import settings

from api.datasets.exceptions import UploadFailedException


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


class JSONGCSService(GCSService):

    @staticmethod
    def is_newline_delimited_json(content) -> bool:
        try:
            for line in content.splitlines():
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
        if isinstance(data, list) and all(isinstance(item, dict) for item in data):
            output = StringIO()
            for item in data:
                output.write(json.dumps(item) + "\n")
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
