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


class NotebookNotFoundException(GenericAPIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = _("Notebook cannot be found. Check if you have permission to access this notebook.")
    default_code = "notebook_not_found"


class NotebookOperationException(GenericAPIException):
    """Base exception for notebook operations."""
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class NotebookStartFailedException(NotebookOperationException):
    default_detail = _("Error starting the notebook.")
    default_code = "notebook_error_starting"


class NotebookStopFailedException(NotebookOperationException):
    default_detail = _("Error stopping the notebook.")
    default_code = "notebook_error_stopping"


class NotebookDestroyFailedException(NotebookOperationException):
    default_detail = _("Error destroying the notebook.")
    default_code = "notebook_error_destroy"


class NotebookInvalidState(NotebookOperationException):
    default_detail = _("Notebook in invalid state.")
    default_code = "notebook_invalid_state"
