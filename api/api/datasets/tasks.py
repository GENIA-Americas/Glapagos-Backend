from celery import shared_task

from api.datasets.services.upload_providers import return_url_provider
from api.datasets.serializers.file import return_serializer_class
from api.datasets.services import FileServiceFactory
from api.users.models.user import User
from api.datasets.models.file import FileUploadStatus
from api.datasets.enums import FileStatus, UploadType


@shared_task
def upload_file_task(validated_data: dict, user_id: str, status_id= int):
    user = User.objects.get(id=user_id)

    if validated_data.get("upload_type", "") == UploadType.URL:
        url = validated_data.get("url", "")
        skip_leading_rows = validated_data.get("skip_leading_rows", 1)
        file_type = validated_data.get("file_type", "")

        provider = return_url_provider(url)
        f = provider.process(url, skip_leading_rows, file_type)

        serializer_class_name = f"{file_type.upper()}Serializer"
        serializer_class = return_serializer_class(serializer_class_name)

        # validates the generated file
        serializer_class(
            data=dict(
                file=f,
                schema=validated_data.get("schema", []),
                autodetect=validated_data.get("autodetect", False)
            )
        ).is_valid(raise_exception=True)
        validated_data["file"] = f

    file_service = FileServiceFactory.get_file_service(
        user=user, **validated_data
    )

    status = FileUploadStatus.objects.get(id=status_id)
    try:
        file_url = file_service.process_file(status_id)
        status.status = FileStatus.UPLOADED
    except Exception as err:
        status.status = FileStatus.ERROR
        status.error = err

    status.save()
    print("succesfully uploaded file ", file_url)

