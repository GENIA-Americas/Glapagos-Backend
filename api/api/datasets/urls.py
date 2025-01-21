# Django
from django.urls import include, path, re_path

# Django Rest Framework
from rest_framework.routers import DefaultRouter

# Views
from api.datasets.views.file import FileUploadStatusViewset, FileViewSet
from api.datasets.views.table import (
    TableViewSet, PrivateTableListView, PublicTableListView, TransformedTableListView
)

router = DefaultRouter()

router.register(r'datasets', FileViewSet, basename='datasets')
router.register(r'upload', FileUploadStatusViewset, basename='upload')
router.register(r'table', TableViewSet, basename='datasets')
router.register(r'table/public', PublicTableListView, basename='datasets')
router.register(r'table/private', PrivateTableListView, basename='datasets')
router.register(r'table/transformed', TransformedTableListView, basename='datasets')

urlpatterns = [
    path('', include(router.urls)),
]
