# Django
from django.urls import include, path

# Django Rest Framework
from rest_framework.routers import DefaultRouter

# Views
from api.datasets.views.file import FileViewSet
from api.datasets.views.table import (
    TableViewSet,
    PrivateTableListView,
    PublicTableListView,
    TransformedTableListView,
)

router = DefaultRouter()

router.register(r"datasets", FileViewSet, basename="datasets-file")
router.register(r"table", TableViewSet, basename="datasets-table")
router.register(r"table/public", PublicTableListView, basename="datasets-table-public")
router.register(r"table/private", PrivateTableListView, basename="datasets-table-private")
router.register(r"table/transformed", TransformedTableListView, basename="datasets-table-transformed")

urlpatterns = [
    path("", include(router.urls)),
]
