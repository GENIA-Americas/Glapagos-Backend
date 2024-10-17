import logging

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .exceptions import GenericAPIException

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler that modifies the default DRF error responses.

    Args:
        exc (Exception): The exception that was raised.
        context (dict): Contextual information about the exception.

    Returns:
        Response: A DRF Response object with customized error details.
    """
    response = exception_handler(exc, context)

    if response is not None:
        request = context.get("request")
        path = request.path if request else "unknown path"

        if isinstance(exc, ValidationError):
            logger.error(f'Validation Error: {exc} in {path}')
        elif isinstance(exc, GenericAPIException):
            logger.error(f'Error: {exc} in {path}. {exc.error}')
        else:
            logger.error(f'Error: {exc} in {path}')
            response.data = {
                'detail': response.data.get("detail", _("An unexpected error occurred.")),
                'status_code': response.status_code
            }
    else:
        view = context.get("view")
        view_info = view.__class__.__name__ if view else "unknown view"

        logger.critical(f'Unhandled error: {exc} in {view_info}')

        response = Response(
            {'detail': _('Internal server error.')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response
