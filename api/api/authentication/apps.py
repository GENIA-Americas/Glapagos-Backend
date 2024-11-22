"""Authentication app"""

# Django
from django.apps import AppConfig


class AuthenticationAppConfig(AppConfig):
    """Authentication app config"""

    name = 'api.authentication'
    verbose_name = 'Authentication'

    def ready(self):
        from . import signals 
