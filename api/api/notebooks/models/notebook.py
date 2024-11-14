from django.db import models

from api.users.models import User
from utils.models import BaseModel


class Notebook(BaseModel):
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=200, blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notebooks', null=True)

    def __str__(self):
        return f"{self.name}"
