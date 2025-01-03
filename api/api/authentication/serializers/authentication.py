"""Authentication serializers"""

# Serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _

from api.users.serializers import UserSerializer
from api.authentication.models import ExternalToken


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get('email')
        try:
            validate_email(email)
        except Exception:
            raise AuthenticationFailed(_('Invalid email format'))

        attrs['email'] = email.lower()

        try:
            data = super().validate(attrs)
        except AuthenticationFailed as exp:
            exp.detail = _("Invalid credentials")
            raise exp

        if not self.user.can_auth():
            token = ExternalToken.objects.filter(user=self.user).first()
            if token:
                if token.is_expired:
                    raise serializers.ValidationError(
                        dict(email=_(
                            "Your account was not validated through your email within the specified time. Before logging in, you must reset your password using the 'Forgot your password' option."))
                    )
                raise serializers.ValidationError(
                    dict(email=_(
                        "You must validate your account through your email before logging in."))
                )
            raise serializers.ValidationError(
                dict(email=_("You could not log in because the registration process was not successfully completed."))
            )
        refresh = self.get_token(self.user)
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        # if you are using double authentication this maybe needed
        # data['username'] = str(self.user.username)

        user_data = UserSerializer(self.user).data
        data['user'] = user_data

        # Add extra responses here
        return data


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh_token = self.context['request'].COOKIES.get(
            settings.SIMPLE_JWT['REFRESH_TOKEN_COOKIE']) or None
        if not attrs['refresh'] and refresh_token:
            attrs['refresh'] = refresh_token
        try:
            data = super().validate(attrs)
        except TokenError:
            raise serializers.ValidationError(
                dict(refresh=_("invalid refresh token or has expired")))
        return data
