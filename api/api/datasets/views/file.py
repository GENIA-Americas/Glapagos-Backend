from django.conf import settings
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.decorators import action

from api.datasets.services.file import upload_to_gcs, mount_file_in_bq
from api.datasets.serializers import FileUploadSerializer
from api.datasets.models import File, Table
from api.datasets.utils import generate_random_string

from api.users.models import User

class FileViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['post'], name='upload_file', url_path='upload_file',
            permission_classes=[])
    def upload_file(self, request, *args, **kwargs):
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file = serializer.validated_data['file']
            extension = serializer.validated_data['extension']
            public = serializer.validated_data['public']

            file_content = file
            bucket_name = settings.GCS_BUCKET
            destination_blob_name = f"{generate_random_string(6)}_{file_content.name}"
            file_url = upload_to_gcs(file_content, bucket_name, destination_blob_name)
            user = User.objects.filter(email='yasmani@themadfox.com').first()

            file = File.objects.create(
                name=destination_blob_name,
                type=extension,
                storage_url=file_url,
                public=public,
                owner=user
            )
            file.save()

            if extension != 'txt':
                table = Table.objects.create(
                    name=destination_blob_name.split(".")[0],
                    dataset_name='glapagos_dataset',
                    file=file
                )
                table.save()
                mount_file_in_bq(table)

            return Response({"file_url": file_url}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

