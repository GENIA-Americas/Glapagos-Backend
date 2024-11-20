from django.utils.translation import gettext_lazy as _
from rest_framework.viewsets import GenericViewSet
from rest_framework import status, permissions, mixins, filters
from rest_framework.decorators import action
from rest_framework.response import Response

from api.notebooks.exceptions import NotebookAlreadyExistsException, NotebookNotFoundException
from api.notebooks.models import Notebook
from api.notebooks.services import VertexInstanceService
from api.notebooks.serializers import NotebookSerializer, StartNotebookSerializer
from api.utils.pagination import StartEndPagination, SearchQueryPagination


class NotebookViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, GenericViewSet):
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

        instance_url = VertexInstanceService.create_instance(instance_id=name, user=user)
        serializer.save(name=name, url=instance_url, owner=user)

    def perform_destroy(self, instance):
        success = VertexInstanceService.destroy_instance(instance_id=instance.name)
        if success:
            instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": _("Notebook '{name}' successfully removed.").format(name=instance.name)},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=["post"],
        name="start",
        url_path="start",
        permission_classes=[permissions.IsAuthenticated],
    )
    def start(self, request, pk, **kwargs):
        user = request.user
        instance = user.notebooks.filter(pk=pk, owner=user).first()
        if not instance:
            raise NotebookNotFoundException()
        instance_url = VertexInstanceService.start_instance(instance_id=instance.name)
        return Response(
            {"detail": _("Notebook started successfully"), "url": instance_url},
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=["post"],
        name="stop",
        url_path="stop",
        permission_classes=[permissions.IsAuthenticated],
    )
    def stop(self, request, pk, **kwargs):
        user = request.user
        instance = user.notebooks.filter(pk=pk, owner=user).first()
        if not instance:
            raise NotebookNotFoundException()
        instance_url = VertexInstanceService.stop_instance(instance_id=instance.name)
        return Response(
            {"detail": _("Notebook stopped successfully"), "url": instance_url},
            status=status.HTTP_200_OK
        )
