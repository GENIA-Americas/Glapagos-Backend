"""Health URLs"""

from django.urls import path
from api.health.views import HealthCheckView

urlpatterns = [
    path("", HealthCheckView.as_view(), name="health-check"),
]
