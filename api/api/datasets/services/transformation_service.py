from abc import ABC, abstractmethod
from typing import List, Dict

from django.conf import settings
from django.utils.translation import gettext_lazy as _
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPIError

from api.users.models import User
from api.datasets.models import Table
from api.datasets.exceptions import TransformationFailedException
from .big_query_service import BigQueryService

from api.datasets.utils import generate_random_string


def apply_transformations(
        table: Table,
        user: User,
        transformations: List[Dict],
        create_table: bool,
        public_destination: bool = None,
) -> Table:
    """
        Applies a series of transformations to a BigQuery table.

        Args:
            table (Table): The table to transform.
            user (User): The user applying the transformations.
            transformations (list): A list of dictionaries with "field", "transformation" and "options".
            create_table (bool): If True, allows table creation on the first transformation.
            public_destination (bool | None): Set new table privacy if create table is True

        Returns:
            Table: The transformed table.

        Raises:
            ValueError: If the transformation class is not found.
    """
    for item in transformations:
        field = item["field"]
        transformation = item["transformation"]
        options = item["options"]

        class_name = f"{transformation}Transformation"
        TransformationClass = globals().get(class_name)

        if TransformationClass is None:
            raise ValueError(_(f"Transformation class not found."))

        obj = TransformationClass(table=table, field=field, user=user,
                                  create_table=create_table,
                                  public_destination=public_destination,
                                  options=options)
        try:
            table = obj.execute()
            create_table = False
        except GoogleAPIError as exp:
            raise TransformationFailedException(
                detail=_("Error while applying transformation {transformation} over {field}").format(
                    transformation=transformation, field=field
                ),
                error=str(exp)
            )

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
    def __init__(self, table: Table, field: str, user: User,
                 create_table: bool, public_destination: bool,
                 options: Dict = None) -> None:
        """
            Initializes the transformation with the given table, field and user
        """
        self.table: Table = table
        self.field: str = field
        self.user: User = user
        self.create_table: bool = create_table
        self.public_destination: bool = public_destination
        self.options: Dict = options

    def get_mode(self) -> bigquery.WriteDisposition:
        """
            Determines the BigQuery write disposition mode.

            Returns:
                bigquery.WriteDisposition: The write mode, either WRITE_EMPTY (for table creation) or WRITE_TRUNCATE.
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

    @abstractmethod
    def update_schema(self) -> List:
        ...

    def execute(self) -> None:
        """
            Executes the transformation by running a BigQuery query and handling table creation if needed.

            Params:
            create_table (bool): If a new table should be created to storage transformation results
            public_destination (bool): Destination privacy. True if destination table should be public.

            Returns:
                Table: The transformed table.

            Raises:
                GoogleAPIError: If there is an error executing the query in BigQuery.
                Exception: For any other unexpected errors.
        """
        bigquery_service = BigQueryService(user=self.user)
        mode: bigquery.WriteDisposition = self.get_mode()
        destination_table: Table = self.table
        if self.create_table:
            dataset_name = settings.BQ_DATASET_ID if self.public_destination else self.user.service_account.dataset_name
            destination_table = Table.objects.create(
                name=f"{self.table.name}_copy_{generate_random_string(5)}",
                dataset_name=dataset_name,
                is_transformed=True,
                parent=self.table,
                file=self.table.file,
                owner=self.user,
                public=self.public_destination,
                schema=self.update_schema()
            )

        job_config = bigquery.QueryJobConfig(
            destination=destination_table.path,
            write_disposition=mode,
        )

        query = self.get_query()
        bigquery_service.query(query=query, job_config=job_config)
        destination_table.mounted = True
        ref = bigquery_service.get_table_reference(destination_table.dataset_name, destination_table.name)
        destination_table.update_table_stats(table_ref=ref)

        return destination_table


class MissingValuesTransformation(Transformation):

    def get_query(self) -> str:
        query = f"""
            SELECT * 
            FROM {self.table.path}
            WHERE {self.field} IS NOT NULL;
        """
        return query

    def update_schema(self) -> List:
        return self.table.schema


class DataTypeConversionTransformation(Transformation):

    def get_query(self) -> str:
        convert_to = self.options.get("convert_to")
        query = None
        if convert_to.upper() in ["INT64", "FLOAT64"]:
            query = f"""
                SELECT 
                    * EXCEPT({self.field}),
                    SAFE_CAST({self.field} AS {convert_to.upper()}) as {self.field}
                FROM {self.table};
            """
        elif convert_to.upper() == "DATETIME":
            query = f"""
                SELECT 
                    * EXCEPT({self.field}),
                    PARSE_DATE('%Y-%m-%d', {self.field}) as {self.field}
                FROM {self.table}
            """

        return query

    def update_schema(self) -> List:
        convert_to = self.options.get("convert_to")
        schema = self.table.schema
        for item in schema:
            if item["column_name"] == self.field:
                item["data_type"] = convert_to.upper()
                break
        return schema
