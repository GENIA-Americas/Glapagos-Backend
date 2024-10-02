from abc import ABC, abstractmethod
from typing import List, Dict

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError

from api.users.models import User
from api.datasets.models import Table
from api.datasets.services.google_cloud_services import search_query, get_table_reference
from api.datasets.utils import generate_random_string


def apply_transformations(
        table: Table,
        user: User,
        transformations: List[Dict[str, str]],
        create_table: bool
) -> Table:
    """
        Applies a series of transformations to a BigQuery table.

        Args:
            table (Table): The table to transform.
            user (User): The user applying the transformations.
            transformations (list): A list of dictionaries with "field" and "transformation".
            create_table (bool): If True, allows table creation on the first transformation.

        Returns:
            Table: The transformed table.

        Raises:
            ValueError: If the transformation class is not found.
    """
    for item in transformations:
        field = item["field"]
        transformation = item["transformation"]

        class_name = f"{transformation}Transformation"
        TransformationClass = globals().get(class_name)

        if TransformationClass is None:
            raise ValueError(_(f"Transformation class not found."))

        obj = TransformationClass(table, field, user=user, create_table=create_table)
        table = obj.execute()
        create_table = False

    return table


class Transformation(ABC):
    """
        Abstract base class for applying transformations to a BigQuery table.

        Args:
            table (Table): The table to transform.
            field (str): The field in the table to be transformed.
            user (User): The user performing the transformation.
            create_table (bool): Flag to indicate if a new table should be created.
    """
    def __init__(self, table: Table, field: str, user: User, create_table: bool) -> None:
        """
            Initializes the transformation with the given table, field, user, and table creation flag.
        """
        self.table = table
        self.field = field
        self.create_table = create_table
        self.user = user

    def get_mode(self):
        """
            Determines the BigQuery write disposition mode.

            Returns:
                str: The write mode, either WRITE_EMPTY (for table creation) or WRITE_TRUNCATE.
        """
        return bigquery.WriteDisposition.WRITE_EMPTY if self.create_table else bigquery.WriteDisposition.WRITE_TRUNCATE


    @abstractmethod
    def get_query(self) -> str:
        """
            Abstract method to define the transformation query.

            Returns:
                str: The query to execute in BigQuery.
        """
        ...

    def execute(self) -> None:
        """
            Executes the transformation by running a BigQuery query and handling table creation if needed.

            Returns:
                Table: The transformed table.

            Raises:
                GoogleAPIError: If there is an error executing the query in BigQuery.
                Exception: For any other unexpected errors.
        """
        client = bigquery.Client()
        mode: bigquery.WriteDisposition = self.get_mode()
        destination_table: Table = self.table
        if self.create_table:
            destination_table = Table.objects.create(
                name=f"{self.table.name}_copy_{generate_random_string(5)}",
                dataset_name=self.table.dataset_name,
                is_transformed=True,
                parent=self.table,
                file=self.table.file
            )
        job_config = bigquery.QueryJobConfig(
            destination=destination_table.path,
            write_disposition=mode,
        )

        query = self.get_query()

        try:
            # query_job = search_query(user=self.user, query=query, job_config=job_config)
            query_job = client.query(query, job_config=job_config)
            query_job.result()
            destination_table.mounted = True
            ref = get_table_reference(settings.BQ_PROJECT_ID, settings.BQ_DATASET_ID, destination_table.name)
            destination_table.update_table_stats(table_ref=ref)
        except GoogleAPIError as e:
            print(f"Error al ejecutar la consulta en BigQuery: {str(e)}")
        except Exception as e:
            print(f"Error inesperado: {str(e)}")

        return destination_table


class MissingValuesTransformation(Transformation):

    def get_query(self) -> str:
        query = f"""
            SELECT * 
            FROM {self.table.path}
            WHERE {self.field} IS NOT NULL;
        """
        return query

