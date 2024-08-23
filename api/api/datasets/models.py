from django.db import models
from utils.models import BaseModel
from api.users.models import User
from api.datasets.enums import DatasetType


class Dataset(BaseModel):
    TYPE_CHOICES = DatasetType.choices

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    storage_id = models.CharField(max_length=255)
    public = models.BooleanField(default=False)
    data_expiration = models.DateTimeField()
    data_location = models.CharField(max_length=1024)
    description = models.TextField()
    number_of_rows = models.IntegerField()
    total_logical_bytes = models.FloatField()
    active_logical_bytes = models.FloatField()
    long_term_logical_bytes = models.FloatField()
    total_physical_bytes = models.FloatField()
    active_physical_bytes = models.FloatField()
    long_term_physical_bytes = models.FloatField()
    time_travel_physical_bytes = models.FloatField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='datasets')

    def get_owner(self):
        return self.owner

    def __str__(self):
        return self.name

