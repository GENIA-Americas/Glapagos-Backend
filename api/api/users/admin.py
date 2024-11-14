"""User models admin."""

# Django
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

# Models
from api.users.models import User


class CustomUserAdmin(UserAdmin):
    """User model admin."""

    list_display = ('id', 'phone_number', 'username', 'first_name', 'last_name', 'is_staff',
                    'deleted')

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': (
            'first_name', 'last_name', 'email', 'gmail', 'organization', 'industry',
            'country_code', 'country', 'phone_number', 'setup_status', 'password_status')}),
        (_('Roles'), {'fields': ('role',)}),
        (_('Deleted'), {'fields': ('deleted',)}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )


admin.site.register(User, CustomUserAdmin)
