# Django
from django.db import models

# Models
from api.utils.models import BaseModel
from api.users.models import User


class Post(BaseModel):
    """
    Post model
    """
    content = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='posts', null=True, blank=True)

    def get_owner(self):
        return self.created_by
