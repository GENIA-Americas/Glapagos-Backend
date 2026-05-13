import django
from unittest.mock import patch, MagicMock

def pytest_configure(config):
    pass

def pytest_sessionstart(session):
    from django.db.models.signals import post_save
    from api.users.signals import create_service_account
    post_save.disconnect(create_service_account, sender=None)
