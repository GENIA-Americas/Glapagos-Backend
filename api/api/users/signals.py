"""User Signals"""

# Channels
from django.db.models.signals import post_save

# Django
from django.dispatch import receiver

# Models
from api.datasets.models import ServiceAccount, ServiceAccountKey
from api.users.models import User

# Utilities
from api.datasets.services import GoogleServiceAccount, GoogleRole, BigQueryService
from api.datasets.utils import generate_random_string

from .exceptions import ServiceAccountCreateException, DatasetCreateException


@receiver(post_save, sender=User)
def create_service_account(sender, instance, created, **kwargs):
    if created:
        # Create account service and key
        try:
            account_name = f"{instance.get_email_name()}{generate_random_string(6)}"
            account = GoogleServiceAccount.create_account(account_name)
            key = GoogleServiceAccount.create_key(account.unique_id)

            GoogleRole.assign_user_rol(account.email)

            key_instance = ServiceAccountKey(
                name=key.name,
                private_key_data=key.private_key_data.decode("utf-8"),
                private_key_type=key.private_key_type,
                valid_after_time=key.valid_after_time,
                valid_before_time=key.valid_before_time,
                key_algorithm=key.key_algorithm,
                key_origin=key.key_origin,
                key_type=key.key_type
            )
            key_instance.save()
        except Exception as exp:
            raise ServiceAccountCreateException(error=str(exp))

        # Create private dataset
        try:
            dataset_name = f"glapagos_private_{account_name}"
            bigquery_service = BigQueryService(user=None)
            bigquery_service.create_dataset(dataset_name)

            # Assign OWNER role to dataset
            GoogleRole.assign_dataset_role(dataset_name=dataset_name, account_email=account.email, role="OWNER")

            account_instance = ServiceAccount(
                name=account.name,
                project_id=account.project_id,
                unique_id=account.unique_id,
                email=account.email,
                etag=account.etag,
                oauth2_client_id=account.oauth2_client_id,
                key=key_instance,
                owner=instance,
                dataset_name=dataset_name,
            )
            account_instance.save()
        except Exception as exp:
            raise DatasetCreateException(error=str(exp))
