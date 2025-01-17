from django.utils.translation import gettext_lazy as _
from django.conf import settings
from rest_framework.viewsets import GenericViewSet
from rest_framework import status, permissions, mixins, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from google.cloud import compute_v1

from api.notebooks.tasks import create_notebook, destroy_notebook, remove_inactive_notebooks, start_notebook, stop_notebook
from api.notebooks.enums import VERTEX_AI_LOCATIONS, AcceleratorType
from api.notebooks.exceptions import NotebookAlreadyExistsException, NotebookNotFoundException, NotebookForbiddenException
from api.notebooks.models import Notebook
from api.notebooks.services import VertexInstanceService, VertexInstanceConfig
from api.notebooks.serializers import NotebookSerializer, AcceleratorSerializer
from api.utils.pagination import StartEndPagination, SearchQueryPagination
from api.users.permissions import InstancePropertyPermission


class NotebookViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet
):
    serializer_class = NotebookSerializer
    model = Notebook
    pagination_class = StartEndPagination
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        user = self.request.user
        return Notebook.objects.filter(owner=user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            results = []
            for notebook in page:
                notebook_data = self.get_serializer(notebook).data
                notebook_data["status"] = VertexInstanceService.get_status(instance_id=notebook_data['name'])
                results.append(notebook_data)

            return self.get_paginated_response(results)

        results = []
        for notebook in queryset:
            notebook_data = self.get_serializer(notebook).data
            notebook_data["status"] = VertexInstanceService.get_status(instance_id=notebook_data['name'])
            results.append(notebook_data)

        return Response(results)

    def perform_create(self, serializer):
        name: str = serializer.validated_data["name"]
        boot_disk: int = serializer.validated_data.get("boot_disk", 150)
        data_disk: int = serializer.validated_data.get("data_disk", 50)
        accelerator_type: int = serializer.validated_data.get("accelerator_type", 0)
        core_count: int = serializer.validated_data.get("core_count", 1)
        zone: str = serializer.validated_data.get("zone", "us-central1-a")

        user = self.request.user
        instance = user.notebooks.first()

        if instance:
            raise NotebookAlreadyExistsException()

        permission = InstancePropertyPermission()
        if not permission.has_permission(self.request, self):
            raise NotebookForbiddenException(
                detail=_("You do not have permission to create a notebook with these properties.")
            )

        create_notebook.apply_async(
            kwargs=dict(
                validated_data=serializer.validated_data,
                user_id=user.id
            )
        )
        serializer.save(name=name, url=None, owner=user, boot_disk=boot_disk,
                        data_disk=data_disk, accelerator_type=accelerator_type,
                        core_count=core_count, zone=zone)

    def perform_destroy(self, instance):
        destroy_notebook.apply_async(
            kwargs=dict(
                instance_name=instance.name
            )
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"detail": _("Notebook '{name}' it's being remove.").format(name=instance.name)},
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
        start_notebook.apply_async(kwargs=dict(instance_name=instance.name))
        return Response(
            {"detail": _("Notebook is starting"), "url": instance.url},
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
        stop_notebook.apply_async(kwargs=dict(instance_name=instance.name))
        return Response(
            {"detail": _("Notebook stopped successfully"), "url": instance.url},
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=["post"],
        name="status",
        url_path="status",
        permission_classes=[permissions.IsAuthenticated],
    )
    def status(self, request, pk, **kwargs):
        user = request.user
        instance = user.notebooks.filter(pk=pk, owner=user).first()
        if not instance:
            raise NotebookNotFoundException()
        instance_status = VertexInstanceService.get_status(instance_id=instance.name)
        return Response(
            {"status": instance_status},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=["post"],
        name="remove_inactives",
        url_path="remove_inactives",
        permission_classes=[permissions.AllowAny],
    )
    def remove_inactives(self, request, **kwargs):
        remove_inactive_notebooks.apply_async()

        return Response(
            {"detail": _("Deleted {deleted_instances} inactive instances").format(deleted_instances=deleted_instances)},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=["get"],
        name="zones",
        url_path="zones",
        permission_classes=[permissions.IsAuthenticated],
    )
    def zones(self, request, **kwargs):
        locations = [loc[0] for loc in VERTEX_AI_LOCATIONS]
        return Response({"zones": locations})

    @action(
        detail=False,
        methods=["get"],
        name="accelerator",
        url_path="accelerator",
        permission_classes=[permissions.IsAuthenticated],
    )
    def accelerators_by_zone(self, request, **kwargs):
        serializer = AcceleratorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        zone = serializer.validated_data['zone']

        client = compute_v1.AcceleratorTypesClient()
        project = settings.BQ_PROJECT_ID

        accelerators = client.list(project=project, zone=zone)
        accelerators_list = []
        for accelerator in accelerators:
            accelerators_list.append({
                "name": accelerator.name,
                "description": accelerator.description,
            })
        return Response({"accelerators": accelerators_list})

    @action(
        detail=False,
        methods=["get"],
        name="accelerator_types",
        url_path="accelerator_types",
        permission_classes=[permissions.IsAuthenticated],
    )
    def accelerator_types(self, request, **kwargs):
        accelerators = [
            {"name": item.name.replace("_", " ").title(), "value": item.value}
            for item in AcceleratorType
        ]
        return Response({"accelerators": accelerators})
