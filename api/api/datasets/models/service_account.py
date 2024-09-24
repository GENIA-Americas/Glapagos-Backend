from django.db import models

# Models
from api.users.models.user import User
from utils.models import BaseModel


class ServiceAccountKey(BaseModel):
    name = models.CharField(max_length=255)
    private_key_data = models.TextField()
    private_key_type = models.CharField(max_length=255)
    valid_after_time = models.CharField(max_length=255)
    valid_before_time = models.CharField(max_length=255)
    key_algorithm = models.CharField(max_length=255)
    key_origin = models.CharField(max_length=255)
    key_type = models.CharField(max_length=255)


class ServiceAccount(BaseModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    key = models.OneToOneField(ServiceAccountKey, on_delete=models.CASCADE)

    name = models.CharField(max_length=255)
    project_id = models.CharField(max_length=255)
    unique_id = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    etag = models.CharField(max_length=255)
    oauth2_client_id = models.CharField(max_length=255)

