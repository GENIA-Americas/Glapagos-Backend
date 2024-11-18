from django.utils.translation import gettext_lazy as _
from rest_framework import status

from api.utils.exceptions import GenericAPIException


class ServiceAccountCreateException(GenericAPIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = _("Error creating service account.")
    default_code = "account_creation_failed"


class DatasetCreateException(GenericAPIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = _("Error creating private dataset.")
    default_code = "dataset_creation_failed"
