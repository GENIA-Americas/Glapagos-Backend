from django.utils.translation import gettext_lazy as _
from rest_framework import status

from api.utils.exceptions import GenericAPIException


class InvalidGoogleAccountException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("User does not have a linked Google account.")
    default_code = "invalid_google_account"


class NotebookAlreadyExistsException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("A notebook already exists for this user.")
    default_code = "notebook_already_exists"
