from django.db import models
from django.core.validators import MinValueValidator

from api.users.models import User
from api.notebooks.enums import ACCELERATOR_TYPE_CHOICES, VERTEX_AI_LOCATIONS
from api.utils.models import BaseModel


class Notebook(BaseModel):
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=200, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notebooks', null=True)
    boot_disk = models.IntegerField(null=True, blank=True, default=150, validators=[MinValueValidator(150)])
    data_disk = models.IntegerField(null=True, blank=True, default=50, validators=[MinValueValidator(50)])
    accelerator_type = models.IntegerField(choices=ACCELERATOR_TYPE_CHOICES, default=0, null=True)
    core_count = models.PositiveIntegerField(default=1, null=True)
    zone = models.CharField(max_length=30, choices=VERTEX_AI_LOCATIONS, default='us-central1-a', null=True)

    def __str__(self):
        return f"{self.name}"
