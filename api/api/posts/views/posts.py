
# Models
from api.posts.models import Post

# Utilities
from api.utils.api.views import crud_from_model
from api.users.permissions import IsAdminPermission, CanCrudPermission, IsSupportReadOnlyPermission
# from rest_framework import permissions

"""
# Rest framework
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response


# Serializers
from api.posts.serializers import PostSerializer
from api.utils.views import BaseViewSet

class PostViewSet(BaseViewSet, viewsets.ModelViewSet):
    
    model = Post
    serializer_class = PostSerializer
    queryset = Post.objects.filter(deleted=False)
    # permission_classes = [HasGroupAccess, IsAuthenticated]
    
    def get_serializer_class(self):
        return super().get_serializer_class()

    def get_queryset(self):
        return super().get_queryset()
"""

PostViewSet = crud_from_model(Post, permissions=[IsAdminPermission | IsSupportReadOnlyPermission | CanCrudPermission])
