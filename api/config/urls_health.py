"""Minimal URL conf for health endpoint tests."""

from django.urls import include, path, re_path
from django.conf import settings

urlpatterns = [
    re_path(settings.API_URI + "/", include("api.health.urls")),
]
