from django.db import models
from api.utils.models import BaseModel
from api.users.models import User
from api.datasets.enums import FileStatus, FileType


class FileUploadStatus(BaseModel):
    status = models.CharField(max_length=20, choices=FileStatus.choices, default=FileStatus.PROCESSING)
    error = models.CharField(max_length=255, null=True)

class File(BaseModel):
    TYPE_CHOICES = FileType.choices
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    storage_url = models.CharField(max_length=255)
    public = models.BooleanField(default=False)
    description = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    status = models.ForeignKey(FileUploadStatus, on_delete=models.CASCADE, default=None, null=True)

    def get_owner(self):
        return self.owner

    def __str__(self):
        return self.name

