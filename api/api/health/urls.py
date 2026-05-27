"""Health check URLs."""

from django.urls import path

from api.health.views import HealthView

urlpatterns = [
    path("health/", HealthView.as_view(), name="health-check"),
]
