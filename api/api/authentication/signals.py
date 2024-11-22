"""Authetication Signals"""

# Channels
from django.db.models.signals import post_save

# Django
from django.dispatch import receiver
from django.conf import settings

# Models
from api.authentication.models import ExternalToken 

from api.utils.sendgrid_mail import send_activate_account_mail, send_change_password_mail
from api.authentication.enums import ExternalTokenType


@receiver(post_save, sender=ExternalToken)
def create_service_account(sender, instance, created, **kwargs):
    if created:
        if instance.type == ExternalTokenType.RECOVER_ACCOUNT:
            data = dict(email=instance.user.email, 
                        url=instance.reset_password_url)
            send_change_password_mail(data, [instance.user.email])

        elif instance.type == ExternalTokenType.VALIDATE_ACCOUNT:
            data = dict(url=instance.activation_url)
            send_activate_account_mail(data, [instance.user.email])

