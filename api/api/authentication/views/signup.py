
# Rest Framework
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

# models
from api.users.models import User
from api.users.serializers import UserSerializer
from api.users.enums import SetUpStatus, PasswordStatus
from api.authentication.enums import ExternalTokenType, ExternalTokenChannel

# Serializers
from api.authentication.serializers import *
from api.authentication.services import signup, authentication, jwt_authentication
from api.utils.decorators import validate_data

# Persmissions
from rest_framework.permissions import AllowAny

# Utilities
from django.conf import settings
from django.shortcuts import render


class SignupViewSet(GenericViewSet):

    @action(detail=False, methods=['post'], serializer_class=SignUpEmailSerializer, permission_classes=[
        AllowAny
    ], name='sign-up', url_path='sign-up')
    @validate_data(out_serializer_class=UserSerializer)
    def sign_up(self, request, validated_data):
        # Users validated by default (Temporal)
        # email = validated_data.pop("email")
        # password = validated_data.pop("password")
        # user = User.objects.create_user(email=email, username=email, password=password, **validated_data)
        # user.setup_status = SetUpStatus.VALIDATED
        # user.password_status = PasswordStatus.ACTIVE
        # user.save()

        # Validate data by email
        email = validated_data.pop("email")
        user_id = signup.signup_request_code(
            email=email,
            resend=False,
            channel=ExternalTokenChannel.CONSOLE,
            user_id=None,
            locale=request.LANGUAGE_CODE,
            **validated_data
        )
        user = User.objects.filter(pk=user_id).first()
        return dict(data=user)

    @action(detail=False, methods=['get'], serializer_class=SignUpValidateCodeSerializer, permission_classes=[
        AllowAny
    ], name='sign-up-validate', url_path='sign-up-validate/(?P<user_id>[^/.]+)/(?P<token>[^/.]+)')
    def sign_up_validate(self, request, user_id=None, token=None):
        data = {
            'user_id': user_id,
            'token': token
        }
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        user.setup_status = SetUpStatus.VALIDATED
        user.save()

        context = {
            'login_url': settings.FRONTEND_LOGIN_URL
        }
        return render(request, 'account_activated.html', context)

    @action(detail=False, methods=['post'], serializer_class=ForgotPasswordValidateCodeSerializer, permission_classes=[
        AllowAny
    ], name='forgot-password-validate', url_path='forgot-password-validate')
    @validate_data()
    def forgot_password_validate(self, request, validated_data):
        password = validated_data['password']
        user = validated_data['user']
        signup.forgot_password_validated(user=user, password=password)
        response = Response(status=200)

        return response 


    @action(detail=False, methods=['post'], serializer_class=ForgotPasswordRequestCodeSerializer, permission_classes=[
        AllowAny
    ], name='forgot-password', url_path='forgot-password')
    @validate_data()
    def forgot_password(self, request, validated_data):
        result = signup.forgot_password_request_code(
            **validated_data, locale=request.LANGUAGE_CODE)
        return dict(data=result)

