from celery import shared_task

from api.users.models.user import User
from api.notebooks.models.notebook import Notebook

from api.notebooks.exceptions import NotebookNotFoundException
from api.notebooks.services.notebook_service import VertexInstanceService, VertexInstanceConfig


@shared_task
def create_notebook(validated_data: dict, user_id: str):
    name: str = validated_data["name"]
    boot_disk: int = validated_data.get("boot_disk", 150)
    data_disk: int = validated_data.get("data_disk", 50)
    accelerator_type: int = validated_data.get("accelerator_type", 0)
    core_count: int = validated_data.get("core_count", 1)
    zone: str = validated_data.get("zone", "us-central1-a")

    config = VertexInstanceConfig(
        boot_disk, data_disk, accelerator_type, core_count, zone
    )

    user = User.objects.get(id=user_id)
    instance_url = VertexInstanceService.create_instance(instance_id=name, config=config, user=user)

    instance = Notebook.objects.get(id=name)
    instance.url = instance_url
    instance.save()

@shared_task
def destroy_notebook(instance_name: str):
    instance = Notebook.objects.get(id=instance_name)
    success = VertexInstanceService.destroy_instance(instance_id=instance_name)
    if success:
        instance.delete()

@shared_task
def stop_notebook(user_id: str, pk: str, instance_name: str):
    user = User.objects.get(id=user_id)
    instance = user.notebooks.filter(pk=pk, owner=user).first()
    if not instance:
        raise NotebookNotFoundException()
    VertexInstanceService.stop_instance(instance_id=instance_name)

@shared_task
def start_notebook(instance_name: str):
    VertexInstanceService.start_instance(instance_id=instance_name)

@shared_task
def remove_inactive_notebooks():
    deleted_instances = 0
    instances = Notebook.objects.all()
    for instance in instances:
        instance_status = VertexInstanceService.get_status(instance.name)
        if instance_status != 'STOPPED':
            continue

        VertexInstanceService.destroy_instance(instance.name)
        instance.delete()
        deleted_instances += 1

