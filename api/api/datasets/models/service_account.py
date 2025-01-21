import secured_fields
from django.db import models

# Models
from api.users.models.user import User
from api.utils.models import BaseModel


class ServiceAccountKey(BaseModel):
    name = models.CharField(max_length=255)
    private_key_data = secured_fields.EncryptedTextField()
    private_key_type = models.CharField(max_length=255)
    valid_after_time = models.CharField(max_length=255)
    valid_before_time = models.CharField(max_length=255)
    key_algorithm = models.CharField(max_length=255)
    key_origin = models.CharField(max_length=255)
    key_type = models.CharField(max_length=255)


class ServiceAccount(BaseModel):
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="service_account")
    key = models.OneToOneField(ServiceAccountKey, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    project_id = models.CharField(max_length=255)
    unique_id = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    etag = models.CharField(max_length=255)
    oauth2_client_id = models.CharField(max_length=255)
    dataset_name = models.CharField(max_length=255, null=True)

