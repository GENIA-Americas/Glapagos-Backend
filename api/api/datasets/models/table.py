import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from google.cloud import bigquery

from api.datasets.exceptions import SchemaUpdateException
from api.datasets.models.file import File
from api.users.models import User
from utils.models import BaseModel

logger = logging.getLogger(__name__)


class Table(BaseModel):
    name = models.CharField(max_length=255)
    dataset_name = models.CharField(max_length=255)
    data_expiration = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    number_of_rows = models.IntegerField(null=True, blank=True)
    total_logical_bytes = models.FloatField(null=True, blank=True)
    mounted = models.BooleanField(default=False)
    public = models.BooleanField(default=False)
    role_asigned = models.BooleanField(default=False)
    is_transformed = models.BooleanField(default=False)
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="child_tables"
    )
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name="tables")
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="tables", null=True
    )
    schema = models.JSONField(null=True, blank=True)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def reference_name(self) -> str:
        parts = self.name.split("_")
        return "_".join(parts[1:]) if len(parts) > 1 else self.name

    @property
    def path(self) -> str:
        return f"{settings.BQ_PROJECT_ID}.{self.dataset_name}.{self.name}"

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def clean(self):
        super().clean()
        if self.parent and self.parent_id == self.pk:
            raise ValidationError(_("A Table cannot have itself as its parent."))

    # ------------------------------------------------------------------
    # BigQuery helpers
    # ------------------------------------------------------------------

    def update_table_stats(self, table_ref) -> None:
        """Fetches live stats from BigQuery and updates the model in one save."""
        client = bigquery.Client()
        table_bq = client.get_table(table_ref)
        self.mounted = True
        self.data_expiration = table_bq.expires
        self.number_of_rows = table_bq.num_rows
        self.total_logical_bytes = table_bq.num_bytes
        self.save(update_fields=["mounted", "data_expiration", "number_of_rows", "total_logical_bytes"])

    def update_schema(self, bigquery_service, force: bool = False) -> None:
        """
        Refreshes the table schema from BigQuery.

        Args:
            bigquery_service: An initialised BigQueryService instance.
            force: If True, skip the notebook-count guard.
        """
        if not force:
            has_notebooks = self.owner.notebooks.exists()
            if not has_notebooks:
                return

        try:
            schema = bigquery_service.get_schema(
                dataset=self.dataset_name, table=self.name
            )
            if schema:
                self.schema = schema
                self.save(update_fields=["schema"])
        except Exception as exc:
            logger.error("Schema update failed for table %s: %s", self.pk, exc)
            raise SchemaUpdateException(error=str(exc))

    def get_column_type(self, column_name: str) -> str | None:
        """Returns the BigQuery data type of a column, or None if not found."""
        if not self.schema:
            return None
        for item in self.schema:
            if item.get("column_name") == column_name:
                return item.get("data_type")
        return None

    # ------------------------------------------------------------------

    def __str__(self) -> str:
        return self.path
