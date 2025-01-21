from typing import Type

from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from rest_framework.viewsets import GenericViewSet
from rest_framework import status, permissions, mixins, filters
from rest_framework.response import Response
from rest_framework.decorators import action

from api.datasets.models.file import FileUploadStatus
from api.datasets.tasks import upload_file_task
from api.utils.sendgrid_mail import send_private_data_mail
from api.datasets.services.upload_providers import return_url_provider
from api.datasets.serializers.file import FileStatusSerializer, JSONSerializer, CSVSerializer, UrlPreviewSerializer, TXTSerializer
from api.datasets.models import File, Table
from api.datasets.services import BigQueryService, FileServiceFactory, StructuredFileService
from api.datasets.serializers import (
    FileSerializer,
    FileUploadSerializer,
    FilePreviewSerializer,
    SearchQuerySerializer,
)
from api.utils.pagination import StartEndPagination, SearchQueryPagination
from api.datasets.enums import UploadType
from api.datasets.serializers.email import PrivateDataAccess


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
        name="authorize-data",
        url_path="authorize-data",
        permission_classes=[permissions.IsAuthenticated],
    )
    def authorize_private_data(self, request, *args, **kwargs):
        serializer = PrivateDataAccess(data=request.data)
        serializer.is_valid(raise_exception=True)

        table = serializer.validated_data.pop("table", Table)
        emails = [table.owner.email] 
        user = request.user

        context = {
            **serializer.validated_data, 
            "first_name": table.owner.first_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "industry": user.industry,
        }

        send_private_data_mail(
            context,
            emails,
            locale=request.LANGUAGE_CODE
        )
        return Response(dict(detail=_("Email send succesfully")), status=status.HTTP_200_OK)

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
        file_type = serializer.validated_data.get("file_type", "")

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

        s_instance = FileStatusSerializer(data=dict())
        s_instance.is_valid()
        s_instance.save()

        upload_file_task.apply_async(
            kwargs=dict(
                validated_data=serializer.validated_data,
                user_id=request.user.id,
                status_id=s_instance.data.get('id')
            )
        )

        return Response({"detail": _("File its being uploaded"), "file_status": s_instance.data}, status=status.HTTP_200_OK)

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
        skip_leading_rows = serializer.validated_data.get('skip_leading_rows')
        file_type = serializer.validated_data['file_type']

        FileService: Type[StructuredFileService] = FileServiceFactory.get_file_service(
            return_instance=False, extension=file_type
        )
        bigquery_format = FileService.preview(data=preview, skip_leading_rows=skip_leading_rows)
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


class FileUploadStatusViewset(mixins.RetrieveModelMixin, GenericViewSet):
    serializer_class = FileStatusSerializer
    model = FileUploadStatus
    permission_classes = [permissions.IsAuthenticated]
    queryset = FileUploadStatus.objects.filter(deleted=False)

