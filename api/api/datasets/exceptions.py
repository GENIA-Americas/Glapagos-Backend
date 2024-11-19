from django.utils.translation import gettext_lazy as _
from rest_framework import status

from api.utils.exceptions import GenericAPIException

class UrlFileNotExistException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Invalid url or file doesn't exist")
    default_code = "file_not_exist"

class UrlProviderException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Couln't identify provider in url, or maybe is not register in providers")
    default_code = "invalid_provider_url"


class InvalidCsvColumnException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Invalid Csv column names")
    default_code = "invalid_csv_columns"


class CsvPreviewFailed(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Csv request failed")
    default_code = "csv_request_failed"


class UrlFolderNameExtractionException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Url name extracted incorrectly")
    default_code = "Url_name_failed"


class InvalidFileException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _(
        "The file structure could not be determined. Please check if the file is corrupted."
    )
    default_code = "invalid_file"


class UploadFailedException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Upload failed")
    default_code = "upload_failed"


class BigQueryMountTableException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("An error occurred while mounting data in BigQuery.")
    default_code = "mount_data_failed"


class QueryFailedException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Query execution failed")
    default_code = "query_failed"


class TransformationFailedException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Transformation failed")
    default_code = "transformation_failed"


class ChartLimitExceededException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Chart limit exceeded: The selected field contains too many distinct categories.")
    default_code = "chart_limit_exceeded"


class SchemaUpdateException(GenericAPIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = _("Schema cannot be updated.")
    default_code = "schema_update_failed"
