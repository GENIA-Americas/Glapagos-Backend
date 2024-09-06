from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from api.datasets.services.file import FileServiceFactory
from api.datasets.serializers import FileUploadSerializer


class FileViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'], name='upload_file', url_path='upload_file',
            permission_classes=[])
    def upload_file(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']
            extension = serializer.validated_data['extension']
            public = serializer.validated_data['public']

            file_service = FileServiceFactory.get_file_service(file, extension, public, request.user)
            try:
                file_url = file_service.process_file()
                return Response({"file_url": file_url}, status=status.HTTP_201_CREATED)
            except Exception as exp:
                raise exp

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

