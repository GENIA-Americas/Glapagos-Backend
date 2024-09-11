"""Dataset models admin."""

# Django
from django.contrib import admin

# Models
from api.contacts.models import Contact


@admin.register(Contact)
class FileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'email',
    )
