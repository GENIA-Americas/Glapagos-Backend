"""Notebooks models admin."""

# Django
from django.contrib import admin

# Models
from .models import Notebook


@admin.register(Notebook)
class NotebookAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'url',
        'owner',
    )
