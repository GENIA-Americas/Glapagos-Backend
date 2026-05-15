"""
Render.com deployment settings for Glapagos demo environment.
Extends production but overrides problematic dependencies.
"""

import os
import dj_database_url
from datetime import timedelta
from .base import *  # noqa
from .base import env

DEBUG = False
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "glapagos-render-demo-key-change-in-prod")
ALLOWED_HOSTS = ["*"]

# Database — Render provides DATABASE_URL
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(DATABASE_URL, conn_max_age=60)
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": "glapagos.sqlite3",
        }
    }

# Static files
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# CORS
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# No S3 for demo — use local storage
DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "media")

# No Redis/Channels for demo
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Admin
ADMIN_URL = "admin/"

# Simple JWT
SIMPLE_JWT.update({
    "ACCESS_TOKEN_LIFETIME": timedelta(days=7),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
})

# Remove daphne — not needed for demo
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "daphne"]
INSTALLED_APPS += ["storages"]

# Email
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_NO_REPLY = "noreply@glapagos.com"
