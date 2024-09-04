from django.db import models
from utils.models import BaseModel
from api.datasets.models.file import File
from django.conf import settings


class Table(BaseModel):
    name = models.CharField(max_length=255)
    dataset_name = models.CharField(max_length=255)
    data_expiration = models.DateTimeField(null=True)
    description = models.TextField(null=True)
    number_of_rows = models.IntegerField(null=True)
    total_logical_bytes = models.FloatField(null=True)
    active_logical_bytes = models.FloatField(null=True)
    long_term_logical_bytes = models.FloatField(null=True)
    total_physical_bytes = models.FloatField(null=True)
    active_physical_bytes = models.FloatField(null=True)
    long_term_physical_bytes = models.FloatField(null=True)
    time_travel_physical_bytes = models.FloatField(null=True)
    mounted = models.BooleanField(default=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='tables')

    @property
    def path(self):
        return f"{settings.BQ_PROJECT_ID}.{self.dataset_name}.{self.name}"

    def __str__(self):
        return f"{self.path}"

