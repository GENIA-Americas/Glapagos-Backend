# Django
from django.urls import include, path, re_path

# Django Rest Framework
from rest_framework.routers import DefaultRouter

# Views
from api.datasets.views.file import FileViewSet

router = DefaultRouter()

router.register(r'datasets', FileViewSet, basename='datasets')

urlpatterns = [
    path('', include(router.urls)),
]
