# Django
from django.urls import include, path, re_path

# Django Rest Framework
from rest_framework.routers import DefaultRouter

# Views
from api.notebooks.views.notebook import NotebookViewSet

router = DefaultRouter()

router.register(r'notebook', NotebookViewSet, basename='notebook')

urlpatterns = [
    path('', include(router.urls)),
]
