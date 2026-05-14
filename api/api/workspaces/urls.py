"""Workspaces URLs"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.workspaces.views import OrganizationViewSet, WorkspaceViewSet

router = DefaultRouter()
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(r"workspaces", WorkspaceViewSet, basename="workspace")

urlpatterns = [
    path("", include(router.urls)),
]
