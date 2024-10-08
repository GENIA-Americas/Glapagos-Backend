from rest_framework.exceptions import APIException
from rest_framework import status


class GenericAPIException(APIException):
    """
    A generic API exception that includes an additional 'error' field to store
    the original exception details.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'An error occurred.'
    default_code = 'generic_error'

    def __init__(self, detail=None, code=None, error=None):
        """
        Initialize the exception with optional detail, code, and error.

        Args:
            detail (str or dict): A human-readable description of the error.
            code (str): A short, machine-readable code for the error.
            error (str): The original exception message or details.
        """
        super().__init__(detail=detail, code=code)
        self.error = error
