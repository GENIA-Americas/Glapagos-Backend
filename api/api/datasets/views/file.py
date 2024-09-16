from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from api.datasets.services.file import FileServiceFactory
from api.datasets.serializers import FileUploadSerializer, FilePreviewSerializer
from api.datasets.utils import csv_parameters_detect, prepare_csv_data_format


class FileViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'], name='upload_file', url_path='upload_file',
            permission_classes=[])
    def upload_file(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file_service = FileServiceFactory.get_file_service(user=request.user, **serializer.validated_data)
            try:
                file_url = file_service.process_file()
                return Response({"file_url": file_url}, status=status.HTTP_201_CREATED)
            except Exception as exp:
                return Response({"detail": _("Error processing request"), "error": str(exp)},
                                status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], name='file-preview', url_path='file-preview',
            permission_classes=[permissions.IsAuthenticated])
    def file_preview(self, request, *args, **kwargs):
        serializer = FilePreviewSerializer(data=request.data)
        if serializer.is_valid():
            try:
                preview = serializer.validated_data['preview']
                bigquery_format = prepare_csv_data_format(data=preview)
                return Response(bigquery_format, status=status.HTTP_200_OK)
            except Exception as exp:
                return Response({"detail": _("Error processing request"), "error": str(exp)},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
