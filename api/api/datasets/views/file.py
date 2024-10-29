
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from rest_framework.viewsets import GenericViewSet
from rest_framework import status, permissions, mixins, filters
from rest_framework.response import Response
from rest_framework.decorators import action

from api.datasets.serializers.upload_providers import return_url_provider
from api.datasets.serializers.file import CSVSerializer, UrlPreviewSerializer
from api.datasets.models import File
from api.datasets.services import BigQueryService, FileServiceFactory
from api.datasets.serializers import (
    FileSerializer,
    FileUploadSerializer,
    FilePreviewSerializer,
    SearchQuerySerializer,
)
from api.datasets.utils import prepare_csv_data_format
from api.utils.pagination import StartEndPagination, SearchQueryPagination
from api.datasets.enums import UploadType


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
        name="url-preview",
        url_path="url-preview",
        permission_classes=[permissions.IsAuthenticated],
    )
    def url_preview(self, request, *args, **kwargs):
        serializer = UrlPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = serializer.validated_data.get("url", "")

        provider = return_url_provider(url)
        provider.preview()
        bigquery_format = prepare_csv_data_format(data=provider.preview_content, skip_leading_rows=1)

        return Response(bigquery_format, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["post"],
        name="upload_file",
        url_path="upload_file",
        permission_classes=[permissions.IsAuthenticated],
    )
    def upload_file(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get("upload_type", "") == UploadType.URL: 
            url = serializer.validated_data.get("url", "")
            skip_leading_rows = serializer.validated_data.get("skip_leading_rows", 1)

            provider = return_url_provider(url)
            f = provider.process(skip_leading_rows)

            # validates the generated file
            CSVSerializer(
                data=dict(
                    file=f,
                    schema=serializer.validated_data.get("schemma", []),
                    autodetect=serializer.validated_data.get("autodetect", False)
                )
            ).is_valid(raise_exception=True)

            serializer.validated_data["file"] = f 

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
                skip_leading_rows = serializer.validated_data["skip_leading_rows"]

                bigquery_format = prepare_csv_data_format(
                    data=preview, skip_leading_rows=skip_leading_rows
                )
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
        pagination_class=SearchQueryPagination,
    )
    def search_query(self, request, *args, **kwargs):
        serializer = SearchQuerySerializer(
            data=request.data, context=dict(request=request)
        )

        if serializer.is_valid():
            try:
                bigquery_service = BigQueryService(user=request.user)
                result = bigquery_service.query(
                    query=serializer.validated_data.get("query", ""),
                    limit=int(request.query_params.get("limit", 20)),
                    offset=int(request.query_params.get("offset", 0)),
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
