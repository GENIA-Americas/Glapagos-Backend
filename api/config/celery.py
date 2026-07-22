"""
Celery application instance.
api/config/celery.py

This module is what compose/local/django/celery/beat/start (and the
worker start script) reference as `-A config.celery_app`. It was
missing entirely before this change, which meant `celery -A
config.celery_app ...` had nothing to import — the worker and beat
containers could not have started.
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("glapagos")

# Read CELERY_* settings from Django settings (see config/settings/base.py).
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks.py in each installed app (api.ai.tasks, etc.).
app.autodiscover_tasks()
