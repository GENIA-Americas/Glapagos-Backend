import logging
import traceback

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

        tb_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))

        if isinstance(exc, ValidationError):
            logger.error(f'Validation Error: {exc} in {path}\n{tb_str}')
        elif isinstance(exc, GenericAPIException):
            logger.error(f'Error: {exc} in {path}. {exc.error}\n{tb_str}')
            response.data = {
                'detail': response.data.get("detail", exc.default_detail),
                'error': exc.error,
                'status_code': exc.status_code
            }
        else:
            logger.error(f'Error: {exc} in {path}\n{tb_str}')
            response.data = {
                'detail': response.data.get("detail", _("An unexpected error occurred.")),
                'status_code': response.status_code
            }
    else:
        view = context.get("view")
        view_info = view.__class__.__name__ if view else "unknown view"

        tb_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        logger.critical(f'Unhandled error: {exc} in {view_info}\n{tb_str}')

        response = Response(
            {'detail': _('Internal server error.')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response

