"""Dataset models admin."""

# Django
from django.contrib import admin

# Models
from .models import File, Table

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'type',
        'public',
        'owner',
    )
