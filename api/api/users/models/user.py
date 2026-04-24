"""User model."""
import logging
import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

from api.utils.models import BaseModel
from api.users.enums import Country, Industry, PasswordStatus, SetUpStatus
from api.users.roles import UserRoles

logger = logging.getLogger(__name__)


class UserManager(BaseUserManager):
    def create_user(self, email=None, username=None, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The email must be set"))

        email = self.normalize_email(email).lower()

        if not username:
            username = email

        user = self.model(email=email, username=username, **extra_fields)
        if not password:
            user.set_unusable_password()
        else:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(
            email=email, password=password, username=email, **extra_fields
        )


class User(BaseModel, AbstractUser):
    """
    User model

    Extends Django's AbstractUser with project-specific fields.
    """

    class Meta:
        permissions = ()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    first_name = models.CharField(max_length=152)
    last_name = models.CharField(max_length=152)
    email = models.EmailField(unique=True)
    gmail = models.EmailField(null=True, blank=True)

    organization = models.CharField(max_length=255, null=True, blank=True)
    industry = models.CharField(
        choices=Industry.choices, max_length=255, null=True, blank=True
    )
    country = models.CharField(
        choices=Country.choices, max_length=255, null=True, blank=True
    )
    country_code = models.CharField(max_length=5)
    phone_number = models.CharField(max_length=16)

    setup_status = models.IntegerField(
        choices=SetUpStatus.choices, default=SetUpStatus.SIGN_UP_VALIDATION
    )
    password_status = models.IntegerField(
        choices=PasswordStatus.choices, default=PasswordStatus.ACTIVE
    )

    preferred_language_code = models.CharField(max_length=16, default="es_ES")
    role = models.CharField(
        choices=UserRoles.choices, max_length=5, blank=True, null=True
    )
    public = models.BooleanField(default=False)

    objects = UserManager()

    generated_email = models.BooleanField(default=False)
    first_sign_up = models.BooleanField(default=True)
    auth0_id = models.CharField(default="", max_length=100, blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    # ------------------------------------------------------------------
    # Ownership helpers
    # ------------------------------------------------------------------

    def get_owner(self):
        return self

    def can_modify(self, user, attributes=None):
        if attributes is None:
            attributes = []

        if self.get_owner() != user:
            return False

        if "password" in attributes and self.password_status != PasswordStatus.CHANGE:
            return False

        return True

    # ------------------------------------------------------------------
    # Status predicates
    # ------------------------------------------------------------------

    def is_public(self) -> bool:
        return self.public

    def is_app_superuser(self) -> bool:
        return self.role == UserRoles.ADMIN

    def can_auth(self) -> bool:
        if self.setup_status == SetUpStatus.SIGN_UP_VALIDATION:
            logger.warning(
                "Login blocked for user %s: setup_status=%s", self.pk, self.setup_status
            )
            return False
        if self.password_status == PasswordStatus.EXTERNAL:
            logger.warning(
                "Login blocked for user %s: password_status=%s", self.pk, self.password_status
            )
            return False
        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def get_email_name(self) -> str:
        """Returns a BigQuery-safe identifier derived from the user's email."""
        return (
            str(self.email)
            .replace("@", "")
            .replace(".", "")
            .replace("_", "")
            .replace("-", "")[:22]
        )

    def __str__(self) -> str:
        return self.email
