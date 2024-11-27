from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from google.cloud import bigquery

from api.datasets.models.file import File
from api.datasets.exceptions import SchemaUpdateException
from api.users.models import User
from utils.models import BaseModel


class Table(BaseModel):
    name = models.CharField(max_length=255)
    dataset_name = models.CharField(max_length=255)
    data_expiration = models.DateTimeField(null=True)
    description = models.TextField(null=True, blank=True)
    number_of_rows = models.IntegerField(null=True)
    total_logical_bytes = models.FloatField(null=True)
    mounted = models.BooleanField(default=False)
    public = models.BooleanField(default=False)
    role_asigned = models.BooleanField(default=False)
    is_transformed = models.BooleanField(default=False)
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, related_name='child_tables')
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='tables')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tables', null=True)
    schema = models.JSONField(null=True, blank=True)

    @property
    def reference_name(self):
        reference_name = self.name

        split_name = reference_name.split("_")
        if len(split_name) > 0:
            return "_".join(split_name[1:])
        return reference_name

    @property
    def path(self):
        return f"{settings.BQ_PROJECT_ID}.{self.dataset_name}.{self.name}"

    def clean(self):
        super().clean()
        if self.parent and self.parent == self:
            raise ValidationError(_("A 'Table' object cannot have itself as its parent."))

    def update_table_stats(self, table_ref):
        client = bigquery.Client()
        table_bq = client.get_table(table_ref)
        self.mounted = True
        self.data_expiration = table_bq.expires
        self.number_of_rows = table_bq.num_rows
        self.total_logical_bytes = table_bq.num_bytes
        self.save()

    def update_schema(self, bigquery_service, force=False):
        if not force:
            has_notebooks = self.owner.notebooks.count() > 0
            if not has_notebooks:
                return

        try:
            schema = bigquery_service.get_schema(
                dataset=self.dataset_name,
                table=self.name
            )
            if schema:
                self.schema = schema
                self.save()
        except Exception as exp:
            raise SchemaUpdateException(error=str(exp))

    def get_column_type(self, column_name: str):
        for item in self.schema:
            if item['column_name'] != column_name:
                continue
            return item['data_type']

    def __str__(self):
        return f"{self.path}"

