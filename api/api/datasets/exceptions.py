from django.utils.translation import gettext_lazy as _
from rest_framework import status

from api.utils.exceptions import GenericAPIException


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
