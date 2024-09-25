from django.db import models
from utils.models import BaseModel
from api.datasets.models.file import File
from django.conf import settings


class Table(BaseModel):
    name = models.CharField(max_length=255)
    dataset_name = models.CharField(max_length=255)
    data_expiration = models.DateTimeField(null=True)
    number_of_rows = models.IntegerField(null=True)
    total_logical_bytes = models.FloatField(null=True)
    mounted = models.BooleanField(default=False)
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='tables')

    @property
    def reference_name(self):
        split_name = self.name.split("_")
        if len(split_name) > 0:
            return "_".join(split_name[1:])
        return self.name

    @property
    def path(self):
        return f"{settings.BQ_PROJECT_ID}.{self.dataset_name}.{self.name}"

    def __str__(self):
        return f"{self.path}"

