import pandas as pd
from io import StringIO

from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from api.datasets.services.file import FileServiceFactory
from api.datasets.serializers import FileUploadSerializer, FilePreviewSerializer


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
                raise exp

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], name='file-preview', url_path='file-preview',
            permission_classes=[permissions.IsAuthenticated])
    def file_preview(self, request, *args, **kwargs):
        serializer = FilePreviewSerializer(data=request.data)
        if serializer.is_valid():
            preview = serializer.validated_data['preview']

            csv_file_like = StringIO(preview)
            df = pd.read_csv(csv_file_like)

            result = []
            for column in df.columns:
                result.append({
                    "column_name": column,
                    "data_type": str(df[column].dtype),
                    "example_values": df[column].head(5).tolist()
                })

            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
