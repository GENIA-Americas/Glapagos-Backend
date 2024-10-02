# Django
from django.urls import include, path 

# Django Rest Framework
from rest_framework.routers import DefaultRouter

# Views
from api.ai.views import AiViewset 

router = DefaultRouter()

router.register(r'ai', AiViewset, basename='ai')

urlpatterns = [
    path('', include(router.urls)),
]
