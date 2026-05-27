"""Main URLs module."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    re_path(settings.API_URI + "/", include("api.users.urls")),
    re_path(settings.API_URI + "/", include("api.events.urls")),
    re_path(settings.API_URI + "/", include("api.datasets.urls")),
    re_path(settings.API_URI + "/", include("api.contacts.urls")),
    re_path(settings.API_URI + "/", include("api.ai.urls")),
    re_path(settings.API_URI + "/", include("api.notebooks.urls")),
    re_path(settings.API_URI + "/", include("api.authentication.urls")),
    re_path(settings.API_URI + "/", include("api.workspaces.urls")),
    re_path(settings.API_URI + "/", include("api.health.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
