from django.utils.translation import gettext_lazy as _
from rest_framework import status

from api.utils.exceptions import GenericAPIException


class UnrelatedTopicException(GenericAPIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = _("Unrelated topic")
    default_code = "unrelated_topic"

