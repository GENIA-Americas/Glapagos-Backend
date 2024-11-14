from rest_framework.viewsets import GenericViewSet
from rest_framework import status, permissions, mixins, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from api.notebooks.exceptions import NotebookAlreadyExistsException
from api.notebooks.models import Notebook
from api.notebooks.services import VertexInstanceService
from api.notebooks.serializers import NotebookSerializer, StartNotebookSerializer
from api.utils.pagination import StartEndPagination, SearchQueryPagination


class NotebookViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    serializer_class = NotebookSerializer
    model = Notebook
    pagination_class = StartEndPagination
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        user = self.request.user
        return Notebook.objects.filter(owner=user)

    def perform_create(self, serializer):
        name = serializer.validated_data["name"]
        user = self.request.user
        instance = user.notebooks.first()

        if instance:
            raise NotebookAlreadyExistsException()

        service = VertexInstanceService()
        instance_url = service.create_instance(instance_id=name, user=user)
        serializer.save(name=name, url=instance_url, owner=user)

    @action(
        detail=False,
        methods=["post"],
        name="start",
        url_path="start",
        permission_classes=[permissions.IsAuthenticated],
    )
    def start(self, request, *args, **kwargs):
        serializer = StartNotebookSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance_id = serializer.validated_data["name"]
        user = request.user

        instance_url = VertexInstanceService.start_instance(instance_id=instance_id, user=user)
        return Response({"url": instance_url}, status=status.HTTP_200_OK)


