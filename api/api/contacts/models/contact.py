from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from api.utils.models import BaseModel
from api.authentication.services.external_token.channels import send_by_channel


class Contact(BaseModel):
    email = models.EmailField(max_length=255, unique=True)

    def __str__(self):
        return self.email


@receiver(post_save, sender=Contact)
def contact_created(sender, instance: Contact, *args, **kwargs):
    try:
        title = "Nuevo contacto"
        message = f"El usuario {instance.email} se ha registrado."
        channel = "console"
        send_by_channel(
            channel, 'es', email=settings.ADMIN_EMAIL, phone_number=None,
            channel_token_message=message, channel_token_title=title
        )
    except Exception as e:
        raise e
