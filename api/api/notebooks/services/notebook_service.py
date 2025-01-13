from dataclasses import dataclass, field

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from google.api_core.retry import Retry
from google.api_core.exceptions import NotFound, ServiceUnavailable, PermissionDenied
from google.cloud import notebooks_v2
from google.cloud.notebooks_v2 import (
    Instance, GceSetup, AcceleratorConfig,
    BootDisk, DataDisk, ServiceAccount,
    CreateInstanceRequest, StartInstanceRequest, StopInstanceRequest
)

from api.users.models import User
from api.notebooks.enums import AcceleratorType
from api.notebooks.exceptions import (
    InvalidGoogleAccountException, NotebookStartFailedException,
    NotebookStopFailedException, NotebookDestroyFailedException,
    NotebookNotFoundException, NotebookInvalidState,
    NotebookCreationFailedException
)


@dataclass
class VertexInstanceConfig:
    boot_disk: int = field(default=150, metadata={"min_value": 150})
    data_disk: int = field(default=50, metadata={"min_value": 50})
    accelerator_type: AcceleratorType = AcceleratorType.ACCELERATOR_TYPE_UNSPECIFIED
    core_count: int = field(default=1, metadata={"min_value": 1})
    zone: str = field(default='us-central1-a')


class VertexInstanceService:
    PROJECT_ID = settings.BQ_PROJECT_ID
    MACHINE_TYPE = "n1-standard-2"
    LOCATION = "us-central1-a"
    IDLE_SHUTDOWN_TIMEOUT = "600"
    OPERATION_DEADLINE_IN_SECONDS = 300
    instances_base_path = f"projects/{PROJECT_ID}/locations/{LOCATION}/instances/"

    @classmethod
    def get_instance(cls, instance_id: str) -> Instance:
        client = notebooks_v2.NotebookServiceClient()
        instance_path = f"{cls.instances_base_path}{instance_id}"
        notebook_instance = client.get_instance(name=instance_path)
        return notebook_instance

    @classmethod
    def create_instance(cls, instance_id: str, config: VertexInstanceConfig, user: User) -> str:
        if not user.gmail:
            raise InvalidGoogleAccountException()
        client = notebooks_v2.NotebookServiceClient()
        parent = f"projects/{cls.PROJECT_ID}/locations/{cls.LOCATION}"

        gce_setup = GceSetup(
            machine_type = cls.MACHINE_TYPE,
            service_accounts = [ServiceAccount(email = user.service_account.email)],
            boot_disk = BootDisk(disk_size_gb=config.boot_disk),
            data_disks = [DataDisk(disk_size_gb=config.data_disk)],
            metadata = {
                "proxy-mode": "service_account",
                "idle-shutdown": "true",
                "idle-shutdown-timeout": cls.IDLE_SHUTDOWN_TIMEOUT,
                "gcs-data-bucket": f"{settings.GCS_NOTEBOOK_BUCKET}/{user.id}"
            }

        )
        if config.accelerator_type != 0:
            gce_setup.accelerator_configs = [AcceleratorConfig(
                type=config.accelerator_type,
                core_count = config.core_count
            )]

        instance = Instance(
            name = instance_id,
            instance_owners=[user.gmail],
            gce_setup = gce_setup
        )

        request = CreateInstanceRequest(
            parent=parent,
            instance_id=instance_id,
            instance=instance,
        )
        try:
            operation = client.create_instance(request=request)
            operation.result()

            retry_policy = Retry(predicate=lambda e: isinstance(e, ValueError), deadline=300)
            instance_url = retry_policy(lambda: cls.check_proxy_uri(instance_id))()
            return instance_url
        except ServiceUnavailable:
            raise NotebookCreationFailedException(detail=_(
                "An instance with these characteristics cannot be created in the zone: {zone}."
            ).format(zone=cls.LOCATION))
        except PermissionDenied:
            raise NotebookCreationFailedException(detail=_(
                "At this time, we do not have the resources available to allocate to an instance with these characteristics in: {zone}."
            ).format(zone=cls.LOCATION))

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
            if notebook_instance.state == notebooks_v2.State.STOPPED:
                request = StartInstanceRequest(name=notebook_instance.name)
                client = notebooks_v2.NotebookServiceClient()
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
            if notebook_instance.state == notebooks_v2.State.ACTIVE:
                request = StopInstanceRequest(name=notebook_instance.name)
                client = notebooks_v2.NotebookServiceClient()
                operation = client.stop_instance(request=request)
                operation.result()

        except Exception as exp:
            raise NotebookStopFailedException(error=str(exp))

    @classmethod
    def destroy_instance(cls, instance_id: str) -> bool:
        try:
            client = notebooks_v2.NotebookServiceClient()
            notebook_instance = cls.get_instance(instance_id)

            if notebook_instance.state == notebooks_v2.State.ACTIVE:
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
