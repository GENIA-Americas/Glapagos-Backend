import logging

from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import RefreshToken

logger = logging.getLogger(__name__)


class CookieOrHeaderAuthentication(JWTAuthentication):
    """
    Accepts a JWT from either:
    - The standard Authorization header (Bearer <token>), or
    - A cookie named by settings.SIMPLE_JWT['ACCESS_TOKEN_COOKIE'].
    """

    def authenticate(self, request):
        header = self.get_header(request)

        if header is None:
            cookie_name = settings.SIMPLE_JWT.get("ACCESS_TOKEN_COOKIE")
            raw_token = request.COOKIES.get(cookie_name) if cookie_name else None
        else:
            raw_token = self.get_raw_token(header)

        if raw_token is None:
            return None

        return self._get_user_from_token(raw_token)

    def _get_user_from_token(self, raw_token):
        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)
        return user, validated_token


def django_user_jwt(user) -> dict:
    """Issues a JWT access/refresh token pair for the given user."""
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
