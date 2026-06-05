"""Users tests."""

# Django
from rest_framework.test import APITestCase
from rest_framework import status
from django.conf import settings

# Models
from api.users.models import User
from api.authentication.models import ExternalToken

# Utils
from api.authentication.enums import ExternalTokenType
from api.users.enums import SetUpStatus, PasswordStatus
from api.users.factories import UserFactory
from api.utils.tests import DefaultTestHelper, response_error
from api.users.roles import UserRoles
from api.authentication.enums import ExternalTokenChannel

# Users helper


class UserTestHelper(DefaultTestHelper):
    default_path = "users"
    model_class = User
    factory = UserFactory
    sample_data = {
        "default": {
            "role": UserRoles.STANDARD,
            "is_active": True,
        },
        "super_admin": {
            "role": UserRoles.ADMIN,
            "is_active": True,
        },
        "john_doe": {
            "password": "SecurePassword#1",
            "setup_status": SetUpStatus.VALIDATED,
            "is_active": True,
            "role": UserRoles.STANDARD,
        },
    }

    create_path = "/" + settings.API_URI + "/auth/sign-up/"
    signup_validate_path = "/" + settings.API_URI + "/auth/sign-up-validate/"
    auth_path = "/" + settings.API_URI + "/auth/token/"
    refresh_path = "/" + settings.API_URI + "/auth/token/refresh/"

    @classmethod
    def force_create(
        cls, client=None, data={}, sample_name="default", force_auth=False
    ):
        # Create new Object with the given data
        sample = cls._get_data(data, sample_name)
        pwd = sample.pop("password", None)
        obj = cls.factory(**sample)
        if pwd:
            obj.set_password(pwd)
            obj.save()

        if force_auth:
            if not client:
                raise Exception("for force auth, client is required")
            client.force_authenticate(user=obj)

        return obj

    @classmethod
    @response_error
    def signup_1_step(cls, client, data=None, sample_name="default"):
        data = cls._get_data(data, sample_name)
        return client.post(cls.create_path, data, format="json")

    @classmethod
    @response_error
    def signup_validate_2_step(cls, client, data=None, sample_name="default"):
        data = cls._get_data(data, sample_name)
        return client.post(cls.signup_validate_path, data, format="json")

    @classmethod
    @response_error
    def update(cls, client, data=None, sample_name="default", headers=None):
        data = cls._get_data(data, sample_name)
        return client.patch(
            cls.signup_update_path, data, format="json", headers=headers
        )

    @classmethod
    @response_error
    def auth(cls, client, data=None):
        return client.post(cls.auth_path, data, format="json")

    @classmethod
    @response_error
    def refresh(cls, client, data=None):
        return client.post(cls.refresh_path, data, format="json")



class AdminUserPostApiTestCase(APITestCase):

    def setUp(self):
        from unittest.mock import patch, MagicMock

        mock_account = MagicMock()
        mock_account.unique_id = "uid123"
        mock_account.email = "test@project.iam.gserviceaccount.com"
        mock_account.name = "projects/p/serviceAccounts/test"
        mock_account.project_id = "project"
        mock_account.etag = "etag"
        mock_account.oauth2_client_id = "oauth2"

        mock_key = MagicMock()
        mock_key.name = "key-name"
        mock_key.private_key_data = b"private-key"
        mock_key.private_key_type = "TYPE_GOOGLE_CREDENTIALS_FILE"
        from django.utils.timezone import now
        mock_key.valid_after_time = now()
        mock_key.valid_before_time = now()
        mock_key.key_algorithm = "KEY_ALG_RSA_2048"
        mock_key.key_origin = "GOOGLE_PROVIDED"
        mock_key.key_type = "USER_MANAGED"

        p1 = patch("api.users.signals.GoogleServiceAccount.create_account", return_value=mock_account)
        p2 = patch("api.users.signals.GoogleServiceAccount.create_key", return_value=mock_key)
        p3 = patch("api.users.signals.GoogleRole.assign_user_rol")
        p4 = patch("api.users.signals.GoogleRole.assign_dataset_role")
        p5 = patch("api.users.signals.BigQueryService")

        for p in [p1, p2, p3, p4, p5]:
            p.start()
            self.addCleanup(p.stop)


    def test_endpoint_responses_code(self):
        from rest_framework_simplejwt.tokens import RefreshToken
        user_data = UserTestHelper.get_sample_data("john_doe")
        user = UserTestHelper.force_create(self.client, data=user_data)
        # Use SimpleJWT directly — avoids Auth0 middleware in tests
        refresh = RefreshToken.for_user(user)
        retrieve_request = UserTestHelper.refresh(
            self.client,
            data=dict(refresh=str(refresh)),
        )
        self.assertEqual(retrieve_request.status_code, status.HTTP_200_OK)

    def test_object_creation(self):
        start_count = UserTestHelper.non_deleted_objects_count()

        signup_data = dict(
            email="testuser@glapagos.com",
            password="SecurePassword#1",
            repeat="SecurePassword#1",
            first_name="Test",
            last_name="User",
            country_code="+1",
            phone_number="1234567890",
        )
        response = UserTestHelper.signup_1_step(self.client, data=signup_data)
        self.assertEqual(UserTestHelper.non_deleted_objects_count(), start_count + 1)
