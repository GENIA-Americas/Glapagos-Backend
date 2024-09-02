from django.conf import settings
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from api.datasets.services.file import upload_to_gcs
from api.datasets.serializers import FileUploadSerializer

from api.datasets.models import File
from api.users.models import User

class FileViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'], name='upload_file', url_path='upload_file',
            permission_classes=[])
    def upload_file(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file_content = serializer.validated_data['file']
            bucket_name = settings.GCS_BUCKET
            destination_blob_name = file_content.name
            file_url = upload_to_gcs(file_content, bucket_name, destination_blob_name)
            user = User.objects.filter(email='yasmani@themadfox.com').first()

            file = File.objects.create(
                name=destination_blob_name,
                type=serializer.validated_data['extension'],
                storage_url=file_url,
                public=serializer.validated_data['public'],
                owner=user
            )
            file.save()

            return Response({"file_url": file_url}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

