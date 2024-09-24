from django.apps import AppConfig


class DatasetsConfig(AppConfig):
    """Datasets app config"""

    name = 'api.datasets'
    verbose_name = 'Datasets'

    def ready(self):
        from . import signals


