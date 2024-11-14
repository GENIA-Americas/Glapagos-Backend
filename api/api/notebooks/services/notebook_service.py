from django.conf import settings
from google.api_core.retry import Retry
from google.cloud import notebooks_v1
from google.cloud.notebooks_v1 import Instance, StartInstanceRequest, StopInstanceRequest

from api.users.models import User
from api.notebooks.exceptions import InvalidGoogleAccountException


class VertexInstanceService:
    project_id = settings.BQ_PROJECT_ID
    machine_type = "n1-standard-2"
    location = "us-central1-a"
    vm_image_project = "ml-images"
    vm_image_name = "c0-deeplearning-common-cpu-v20230925-debian-10"
    idle_shutdown_timeout = "300"
    # accelerator_config = {"type": notebooks_v1.Instance.AcceleratorType.NVIDIA_TESLA_T4, "core_count": 1},
    accelerator_config = {}

    @classmethod
    def create_instance(cls, instance_id: str, user: User) -> str:
        if not user.gmail:
            raise InvalidGoogleAccountException()
        client = notebooks_v1.NotebookServiceClient()
        parent = f"projects/{cls.project_id}/locations/{cls.location}"

        instance = Instance(
            machine_type=cls.machine_type,
            accelerator_config=cls.accelerator_config,
            vm_image={
                "project": cls.vm_image_project,
                "image_name": cls.vm_image_name
            },
            metadata={
                "proxy-mode": "service_account",
                "idle-shutdown-timeout": cls.idle_shutdown_timeout
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

        instance_path = f"{parent}/instances/{instance_id}"
        retry_policy = Retry(predicate=lambda e: isinstance(e, ValueError), deadline=300)
        instance_url = retry_policy(lambda: cls.check_proxy_uri(instance_path))()
        return instance_url

    @staticmethod
    def check_proxy_uri(instance_path: str) -> str:
        client = notebooks_v1.NotebookServiceClient()
        notebook_instance = client.get_instance(name=instance_path)
        if notebook_instance.proxy_uri:
            return notebook_instance.proxy_uri
        else:
            raise ValueError("proxy_uri not available")

    @classmethod
    def start_instance(cls, instance_id: str, user: User) -> str:
        try:
            client = notebooks_v1.NotebookServiceClient()
            instance_path = f"projects/{cls.project_id}/locations/{cls.location}/instances/{instance_id}"
            notebook_instance = client.get_instance(name=instance_path)
            if notebook_instance.state == notebooks_v1.Instance.State.STOPPED:
                request = StartInstanceRequest({"name": instance_path})
                operation = client.start_instance(request=request)
                operation.result()

            retry_policy = Retry(predicate=lambda e: isinstance(e, ValueError), deadline=300)
            instance_url = retry_policy(lambda: cls.check_proxy_uri(instance_path))()
            return instance_url
        except Exception as exp:
            raise exp
