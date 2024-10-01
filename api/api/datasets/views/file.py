from django.utils.translation import gettext_lazy as _
from django.db.models import Q 
from rest_framework.viewsets import GenericViewSet
from rest_framework import pagination, status, permissions, mixins, filters
from rest_framework.response import Response
from rest_framework.decorators import action

from api.datasets.services.google_cloud_services import search_query
from api.datasets.models import File
from api.datasets.services.file import FileServiceFactory
from api.datasets.serializers import (
    FileSerializer,
    FileUploadSerializer,
    FilePreviewSerializer,
    SearchQuerySerializer,
)
from api.datasets.utils import prepare_csv_data_format
from api.utils.pagination import StartEndPagination

class SearchQueryPagination(pagination.LimitOffsetPagination):
    def paginate_queryset(self, queryset, request, view=None):
        self.request = request
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None

        self.count = self.get_count(queryset)
        print(self.count)
        self.offset = self.get_offset(request)

        if self.count == 0 or self.offset > self.count:
            return []

        return queryset 

    def get_count(self, queryset):
        return queryset.total_rows

class FileViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = FileSerializer
    serializer_classes = dict(
        list=FileSerializer,
    )
    model = File
    pagination_class = StartEndPagination
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        user = self.request.user
        return File.objects.filter(Q(public=True) | Q(owner=user))

    @action(
        detail=False,
        methods=["post"],
        name="upload_file",
        url_path="upload_file",
        permission_classes=[],
    )
    def upload_file(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file_service = FileServiceFactory.get_file_service(
                user=request.user, **serializer.validated_data
            )
            try:
                file_url = file_service.process_file()
                return Response({"file_url": file_url}, status=status.HTTP_201_CREATED)
            except Exception as exp:
                return Response(
                    {"detail": _("Error processing request"), "error": str(exp)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["post"],
        name="file-preview",
        url_path="file-preview",
        permission_classes=[permissions.IsAuthenticated],
    )
    def file_preview(self, request, *args, **kwargs):
        serializer = FilePreviewSerializer(data=request.data)
        if serializer.is_valid():
            try:
                preview = serializer.validated_data["preview"]
                bigquery_format = prepare_csv_data_format(data=preview)
                return Response(bigquery_format, status=status.HTTP_200_OK)
            except Exception as exp:
                return Response(
                    {"detail": _("Error processing request"), "error": str(exp)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["post"],
        name="search_query",
        url_path="search_query",
        permission_classes=[permissions.IsAuthenticated],
        pagination_class=SearchQueryPagination
    )
    def search_query(self, request, *args, **kwargs):
        serializer = SearchQuerySerializer(
            data=request.data, context=dict(request=request)
        )

        if serializer.is_valid():
            try:
                result = search_query(
                    request.user, serializer.validated_data.get("query", ""),
                    limit = int(request.query_params.get("limit", 20)),
                    offset = int(request.query_params.get("offset", 0)) 
                )
                self.paginate_queryset(result)
                return self.get_paginated_response(result)
            except Exception as exp:
                return Response(
                    {"detail": _("Error processing request"), "error": str(exp)},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

