import logging
from enum import Enum

from api.utils.sendgrid_mail import (
    send_change_password_mail,
    send_activate_account_mail,
)
from api.users.enums import SetUpStatus, PasswordStatus
from api.users.models import User
from api.authentication.enums import ExternalTokenType
from api.authentication.models import ExternalToken

logger = logging.getLogger(__name__)

# class SetUpStatus(Enum):
#     SIGN_UP_VALIDATION = 0
#     VALIDATED = 1


def destroy_token_by(
    phone_number=None, email=None, token_type=ExternalTokenType.VALIDATE_ACCOUNT
):
    queryset = ExternalToken.objects.filter(type=token_type)

    if type(phone_number) is not None:
        queryset = queryset.filter(user__phone_number=phone_number)

    if type(email) is not None:
        queryset = queryset.filter(user__email=email)

    queryset.delete()


def create_token(
    user_id, channel, token_type=ExternalTokenType.VALIDATE_ACCOUNT, locale: str = "en"
):

    token = ExternalToken.objects.create(
        type=token_type, user_id=user_id, channel=channel
    )

    # Email sending is best-effort: don't block account creation if the
    # mail provider is unavailable (e.g. SendGrid trial expired). The
    # activation URL is still printed via the CONSOLE channel below, so
    # accounts remain usable — this just means the automated email isn't
    # sent until email delivery is properly configured/paid for.
    if token.type == ExternalTokenType.RECOVER_ACCOUNT:
        data = dict(email=token.user.email, url=token.reset_password_url)
        try:
            send_change_password_mail(data, [token.user.email], locale=locale)
        except Exception as exc:
            logger.warning("Failed to send password-reset email: %s", exc)

    elif token.type == ExternalTokenType.VALIDATE_ACCOUNT:
        data = dict(url=token.activation_url)
        try:
            send_activate_account_mail(data, [token.user.email], locale=locale)
        except Exception as exc:
            logger.warning("Failed to send activation email: %s", exc)

    return token.resend_at, token.expires_at


def create_user(*args, **kwargs):
    user = User.objects.create_user(*args, **kwargs)
    return user.id


def signup_request_code(
    email,
    resend,
    channel,
    user_id,
    locale="en",
    **kwargs,
):
    if not resend:
        password = kwargs.pop("password")
        user_id = create_user(email=email, username=email, password=password, **kwargs)
    else:
        destroy_token_by(email=email)
    create_token(user_id=user_id, channel=channel, locale=locale)
    return user_id


def signup_validated(
    user: User,
):
    ExternalToken.objects.filter(
        user=user, type=ExternalTokenType.VALIDATE_ACCOUNT
    ).delete()
    user.setup_status = SetUpStatus.VALIDATED
    user.password_status = PasswordStatus.ACTIVE
    user.save()
    return True


def signup_completed(
    set_user_setup_status,
    user_id,
):
    set_user_setup_status(user_id, SetUpStatus.VALIDATED)
    return True


def forgot_password_request_code(
    resend,
    channel,
    user_id,
    email=None,
    locale="en",
    **kwargs,
):
    if not user_id:
        return

    if resend:
        destroy_token_by(email=email, token_type=ExternalTokenType.RECOVER_ACCOUNT)
    create_token(
        user_id=user_id,
        channel=channel,
        token_type=ExternalTokenType.RECOVER_ACCOUNT,
        locale=locale,
    )
    return {
        "channel": channel,
        "resend": resend,
    }


def forgot_password_validated(
    user: User,
    password: str,
):
    ExternalToken.objects.filter(
        user=user, type=ExternalTokenType.RECOVER_ACCOUNT
    ).delete()
    user.password_status = PasswordStatus.ACTIVE
    user.set_password(password)
    user.setup_status = SetUpStatus.VALIDATED
    user.save()
    return True
