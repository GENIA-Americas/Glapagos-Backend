from django.utils.translation import gettext_lazy as _
from rest_framework import status

from api.utils.exceptions import GenericAPIException


class QueryFailedException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Query execution failed")
    default_code = "query_failed"


class TransformationFailedException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Transformation failed")
    default_code = "transformation_failed"
