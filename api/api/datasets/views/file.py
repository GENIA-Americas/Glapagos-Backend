import logging
from typing import Type

from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import filters, mixins, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from api.datasets.enums import UploadType
from api.datasets.models import File, Table
from api.datasets.serializers import (
    FilePreviewSerializer,
    FileSerializer,
    FileUploadSerializer,
    SearchQuerySerializer,
)
from api.datasets.serializers.email import PrivateDataAccess
from api.datasets.serializers.file import (
    CSVSerializer,
    JSONSerializer,
    TXTSerializer,
    UrlPreviewSerializer,
)
from api.datasets.services import BigQueryService, FileServiceFactory, StructuredFileService
from api.datasets.services.upload_providers import return_url_provider
from api.utils.pagination import SearchQueryPagination, StartEndPagination
from api.utils.sendgrid_mail import send_private_data_mail

logger = logging.getLogger(__name__)

_UPLOAD_SERIALIZER_MAP = {
    "CSV": CSVSerializer,
    "JSON": JSONSerializer,
    "TXT": TXTSerializer,
}


class FileViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = FileSerializer
    serializer_classes = dict(list=FileSerializer)
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
        name="authorize-data",
        url_path="authorize-data",
        permission_classes=[permissions.IsAuthenticated],
    )
    def authorize_private_data(self, request, *args, **kwargs):
        serializer = PrivateDataAccess(data=request.data)
        serializer.is_valid(raise_exception=True)

        table: Table = serializer.validated_data.pop("table")
        user = request.user

        context = {
            **serializer.validated_data,
            "first_name": table.owner.first_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "industry": user.industry,
        }

        send_private_data_mail(context, [table.owner.email], locale=request.LANGUAGE_CODE)
        return Response(
            {"detail": _("Email sent successfully")}, status=status.HTTP_200_OK
        )

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

        url = serializer.validated_data["url"]
        file_type = serializer.validated_data["file_type"]

        provider = return_url_provider(url)
        preview = provider.preview(url, file_type)
        return Response(preview, status=status.HTTP_200_OK)

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

        if serializer.validated_data.get("upload_type") == UploadType.URL:
            url = serializer.validated_data["url"]
            skip_leading_rows = serializer.validated_data.get("skip_leading_rows", 1)
            file_type = serializer.validated_data["file_type"]

            provider = return_url_provider(url)
            f = provider.process(url, skip_leading_rows, file_type)

            # Validate the file via the appropriate serializer
            file_serializer_cls = _UPLOAD_SERIALIZER_MAP.get(file_type.upper())
            if file_serializer_cls is None:
                return Response(
                    {"detail": _("Unsupported file type: {}").format(file_type)},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            file_serializer_cls(
                data={
                    "file": f,
                    "schema": serializer.validated_data.get("schema", []),
                    "autodetect": serializer.validated_data.get("autodetect", False),
                }
            ).is_valid(raise_exception=True)

            serializer.validated_data["file"] = f

        file_service = FileServiceFactory.get_file_service(
            user=request.user, **serializer.validated_data
        )
        if file_service is None:
            return Response(
                {"detail": _("Unsupported file type.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_url = file_service.process_file()
        return Response(
            {"detail": _("File uploaded successfully"), "file_url": file_url},
            status=status.HTTP_201_CREATED,
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
        serializer.is_valid(raise_exception=True)

        preview = serializer.validated_data["preview"]
        skip_leading_rows = serializer.validated_data.get("skip_leading_rows")
        file_type = serializer.validated_data["file_type"]

        FileService: Type[StructuredFileService] = FileServiceFactory.get_file_service(
            return_instance=False, extension=file_type
        )
        bigquery_format = FileService.preview(
            data=preview, skip_leading_rows=skip_leading_rows
        )
        return Response(bigquery_format, status=status.HTTP_200_OK)

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
            data=request.data, context={"request": request}
        )
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            bigquery_service = BigQueryService(user=request.user)
            result = bigquery_service.query(
                query=serializer.validated_data.get("query", ""),
                limit=int(request.query_params.get("limit", 20)),
                offset=int(request.query_params.get("offset", 0)),
            )
            self.paginate_queryset(result)
            return self.get_paginated_response(result)
        except Exception as exc:
            logger.error("search_query failed: %s", exc, exc_info=True)
            return Response(
                {"detail": _("Error processing request"), "error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
