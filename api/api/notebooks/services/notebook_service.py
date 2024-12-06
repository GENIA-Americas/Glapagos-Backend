from django.conf import settings
from django.utils.translation import gettext_lazy as _
from google.api_core.retry import Retry
from google.api_core.exceptions import NotFound
from google.cloud import notebooks_v1
from google.cloud.notebooks_v1 import Instance, StartInstanceRequest, StopInstanceRequest

from api.users.models import User
from api.notebooks.exceptions import (
    InvalidGoogleAccountException, NotebookStartFailedException,NotebookStopFailedException,
    NotebookDestroyFailedException, NotebookNotFoundException, NotebookInvalidState
)


class VertexInstanceService:
    PROJECT_ID = settings.BQ_PROJECT_ID
    MACHINE_TYPE = "n1-standard-2"
    LOCATION = "us-central1-a"
    VM_IMAGE_PROJECT = "ml-images"
    VM_IMAGE_NAME = "c0-deeplearning-common-cpu-v20230925-debian-10"
    IDLE_SHUTDOWN_TIMEOUT = "600"
    # accelerator_config = {"type": notebooks_v1.Instance.AcceleratorType.NVIDIA_TESLA_T4, "core_count": 1},
    accelerator_config = {}
    OPERATION_DEADLINE_IN_SECONDS = 300
    instances_base_path = f"projects/{PROJECT_ID}/locations/{LOCATION}/instances/"

    @classmethod
    def get_instance(cls, instance_id: str) -> Instance:
        client = notebooks_v1.NotebookServiceClient()
        instance_path = f"{cls.instances_base_path}{instance_id}"
        notebook_instance = client.get_instance(name=instance_path)
        return notebook_instance

    @classmethod
    def create_instance(cls, instance_id: str, user: User) -> str:
        if not user.gmail:
            raise InvalidGoogleAccountException()
        client = notebooks_v1.NotebookServiceClient()
        parent = f"projects/{cls.PROJECT_ID}/locations/{cls.LOCATION}"

        instance = Instance(
            machine_type=cls.MACHINE_TYPE,
            accelerator_config=cls.accelerator_config,
            vm_image={
                "project": cls.VM_IMAGE_PROJECT,
                "image_name": cls.VM_IMAGE_NAME
            },
            boot_disk_size_gb = 50,
            data_disk_size_gb = 50,
            metadata={
                "proxy-mode": "service_account",
                "idle-shutdown": "true",
                "idle-shutdown-timeout": cls.IDLE_SHUTDOWN_TIMEOUT,
                "gcs-data-bucket": f"{settings.GCS_NOTEBOOK_BUCKET}/{user.id}"
            },
            instance_owners=[user.gmail],
            service_account=user.service_account.email
        )

        operation = client.create_instance(
            parent=parent,
            instance_id=instance_id,
            instance=instance,
        )
        operation.result()

        retry_policy = Retry(predicate=lambda e: isinstance(e, ValueError), deadline=300)
        instance_url = retry_policy(lambda: cls.check_proxy_uri(instance_id))()
        return instance_url

    @classmethod
    def check_proxy_uri(cls, instance_id: str) -> str:
        notebook_instance = cls.get_instance(instance_id)
        if notebook_instance.proxy_uri:
            return notebook_instance.proxy_uri
        else:
            raise ValueError("proxy_uri not available")

    @classmethod
    def get_status(cls, instance_id: str) -> str:
        try:
            notebook_instance = cls.get_instance(instance_id)
            return str(notebook_instance.state).split(".")[1]
        except Exception as exp:
            raise NotebookInvalidState(error=str(exp))

    @classmethod
    def start_instance(cls, instance_id: str) -> str:
        try:
            notebook_instance = cls.get_instance(instance_id)
            if notebook_instance.state == notebooks_v1.Instance.State.STOPPED:
                request = StartInstanceRequest(name=notebook_instance.name)
                client = notebooks_v1.NotebookServiceClient()
                operation = client.start_instance(request=request)
                operation.result()

            retry_policy = Retry(predicate=lambda e: isinstance(e, ValueError), deadline=300)
            instance_url = retry_policy(lambda: cls.check_proxy_uri(instance_id))()
            return instance_url
        except Exception as exp:
            raise NotebookStartFailedException(error=str(exp))

    @classmethod
    def stop_instance(cls, instance_id: str) -> None:
        try:
            notebook_instance = cls.get_instance(instance_id)
            if notebook_instance.state == notebooks_v1.Instance.State.ACTIVE:
                request = notebooks_v1.StopInstanceRequest(name=notebook_instance.name)
                client = notebooks_v1.NotebookServiceClient()
                operation = client.stop_instance(request=request)
                operation.result()

        except Exception as exp:
            raise NotebookStopFailedException(error=str(exp))

    @classmethod
    def destroy_instance(cls, instance_id: str) -> bool:
        try:
            client = notebooks_v1.NotebookServiceClient()
            notebook_instance = cls.get_instance(instance_id)

            if notebook_instance.state == notebooks_v1.Instance.State.ACTIVE:
                cls.stop_instance(instance_id)

            operation = client.delete_instance(name=notebook_instance.name)
            operation.result()
            return True

        except NotFound:
            raise NotebookNotFoundException(
                detail=_("Instance {instance_id} not found").format(instance_id=instance_id),
            )
        except Exception as exp:
            raise NotebookDestroyFailedException(error=str(exp))
