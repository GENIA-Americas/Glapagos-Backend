"""Dataset models admin."""

# Django
from django.contrib import admin

# Models
from .models import File, Table, ServiceAccount, ServiceAccountKey

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'type',
        'public',
        'owner',
    )

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'dataset_name',
        'mounted',
    )

@admin.register(ServiceAccountKey)
class ServiceAccountKeyAdmin(admin.ModelAdmin):
    list_display = ["name", "private_key_data", "private_key_type"] 

@admin.register(ServiceAccount)
class ServiceAccountAdmin(admin.ModelAdmin):
    list_display = ["owner", "name", "unique_id", "email", "project_id"] 

