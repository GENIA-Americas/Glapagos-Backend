"""Datasets Signals"""

# Channels
from django.db.models.signals import post_save

# Django
from django.dispatch import receiver

# Models
from api.datasets.models.service_account import ServiceAccount
from api.datasets.models import Table

# Utilities
from api.datasets.services.accounts import GoogleRole

@receiver(post_save, sender=Table)
def grant_table_role(sender, instance, created, **kwargs):
    if created:
        account = ServiceAccount.objects.filter(owner=instance.file__owner).first()
        GoogleRole.assign_table_role(instance.name, account.email)

