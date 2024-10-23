from django.utils.translation import gettext_lazy as _
from rest_framework import status

from api.utils.exceptions import GenericAPIException

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


class QueryFailedException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Query execution failed")
    default_code = "query_failed"


class TransformationFailedException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Transformation failed")
    default_code = "transformation_failed"
