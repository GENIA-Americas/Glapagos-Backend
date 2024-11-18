"""User models admin."""

# Django
from django.contrib import admin

# Models
from api.posts.models import *

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'content',
        'created_by',
    )
