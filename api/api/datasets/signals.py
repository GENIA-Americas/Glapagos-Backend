"""Datasets Signals"""

# Channels
from django.db.models.signals import post_save

# Django
from django.dispatch import receiver

# Models
from api.datasets.models import Table

# Utilities
from api.datasets.services import GoogleRole


@receiver(post_save, sender=Table)
def grant_table_role(sender, instance, created, **kwargs):
    if instance.mounted and not instance.role_asigned:
        account = instance.file.owner.service_account
        GoogleRole.assign_table_role(instance.path, account.email)
        instance.role_asigned = True
        instance.save()

