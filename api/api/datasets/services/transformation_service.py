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

from api.utils.basics import generate_random_string


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
    bigquery_service = BigQueryService(user=user)
    for item in transformations:
        field = item["field"]
        transformation = item["transformation"]
        options = item.get("options")

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
            table.update_schema(bigquery_service, force=True)
            raise TransformationFailedException(
                detail=_("Error while applying transformation {transformation} over {field}").format(
                    transformation=transformation, field=field
                ),
                error=str(exp)
            )
    table.update_schema(bigquery_service, force=True)
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

    def generate_table_name(self):
        """
            Generates a new table name based on the current table name.

            If the current table name contains the substring '_copy_', the new table name
            will preserve the part before the last '_copy_' and append a new '_copy_'
            followed by a random 5-character string.

            If the current table name does not contain '_copy_', the function appends
            '_copy_' followed by a random 5-character string to the original name.

            Returns:
                str: The newly generated table name.
        """
        split_name: List = self.table.name.split("_copy_")
        if len(split_name) > 1:
            return f"{'_'.join(split_name[:-1])}_copy_{generate_random_string(5)}"
        return f"{self.table.name}_copy_{generate_random_string(5)}"

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

        if not self.table.schema:
            schema = bigquery_service.get_schema(
                dataset=self.table.dataset_name,
                table=self.table.name
            )
            if not schema:
                raise TransformationFailedException(_("No schema info for this dataset."))

        destination_table = self.table
        if self.create_table:
            dataset_name = settings.BQ_DATASET_ID if self.public_destination else self.user.service_account.dataset_name

            destination_table = Table.objects.create(
                name=self.generate_table_name(),
                dataset_name=dataset_name,
                is_transformed=True,
                parent=self.table,
                file=self.table.file,
                owner=self.user,
                public=self.public_destination,
                schema=self.table.schema,
                description=self.table.description,
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
    """
    Transformation class to filter out rows where a specific field contains NULL values.
    """

    def get_query(self) -> str:
        """
        Generates a SQL query that selects all rows where the specified field is not NULL.

        Returns:
            str: SQL query string to filter out rows with NULL values in the specified field.
        """
        query = f"""
            SELECT * 
            FROM `{self.table.path}`
            WHERE `{self.field}` IS NOT NULL;
        """
        return query


class DataTypeConversionTransformation(Transformation):
    """
    Transformation class to convert the data type of specific field to a target type.
    """

    def get_query(self) -> str:
        """
        Generates a SQL query to convert the data type of the specified field.

        The conversion type is obtained from the `options` dictionary. Supported types
        include INT64, FLOAT64, DATE and DATETIME.

        Returns:
            str: SQL query to cast the field to the new data type or parse it to a DATE format.
        """
        convert_from = self.table.get_column_type(column_name=self.field)
        if not convert_from:
            raise TransformationFailedException(
                _("No data info for the field {field} in the schema.")
            ).format(field=self.field)

        convert_to = self.options.get("convert_to")
        query = None

        if convert_from.upper() == "STRING":
            if convert_to.upper() == "DATETIME":
                query = f"""
                    SELECT 
                        * EXCEPT(`{self.field}`),
                        PARSE_DATETIME('%Y-%m-%d %H:%M:%S', `{self.field}`) as `{self.field}`
                    FROM `{self.table.path}`
                """
            elif convert_to.upper() == "DATE":
                query = f"""
                    SELECT 
                        * EXCEPT(`{self.field}`),
                        PARSE_DATE('%Y-%m-%d', `{self.field}`) as `{self.field}`
                    FROM `{self.table.path}`
                """
            elif convert_to.upper() in ["INT64", "FLOAT64"]:
                query = f"""
                        SELECT 
                            * EXCEPT(`{self.field}`),
                            SAFE_CAST(`{self.field}` AS {convert_to.upper()}) as `{self.field}`
                        FROM `{self.table.path}`;
                    """

            return query

        elif convert_to.upper() == "STRING":
            if convert_from.upper() == "DATETIME":
                query = f"""
                    SELECT 
                        * EXCEPT(`{self.field}`),
                        FORMAT_DATETIME('%Y-%m-%d %H:%M:%S', `{self.field}`) as `{self.field}`
                    FROM `{self.table.path}`
                """
            elif convert_from.upper() == "DATE":
                query = f"""
                    SELECT 
                        * EXCEPT(`{self.field}`),
                        FORMAT_DATE('%Y-%m-%d', `{self.field}`) as `{self.field}`
                    FROM `{self.table.path}`
                """
            elif convert_from.upper() in ["INT64", "FLOAT64"]:
                query = f"""
                        SELECT 
                            * EXCEPT(`{self.field}`),
                            SAFE_CAST(`{self.field}` AS {convert_to.upper()}) as `{self.field}`
                        FROM `{self.table.path}`;
                    """

            return query

        raise TransformationFailedException(
            detail=_("Cannot convert to {to_type} from a {from_type} field.").format(
                to_type=convert_to.upper(), from_type=convert_from.upper()
            )
        )


class RemoveDuplicatesTransformation(Transformation):
    """
    Transformation class to remove duplicate rows based on a specified field.
    """

    def get_query(self) -> str:
        """
        Generates a SQL query to remove duplicate rows from the table.

        The query assigns a row number to each row partitioned by the specified field
        and keeps only the first occurrence of each partition.

        Returns:
            str: SQL query that removes duplicates based on the specified field.
        """
        query = f"""
            WITH numbered_rows AS (
              SELECT 
                *,
                ROW_NUMBER() OVER (PARTITION BY `{self.field}` ORDER BY `{self.field}`) AS row_num
              FROM `{self.table.path}`
            )

            SELECT *
            FROM numbered_rows
            WHERE row_num = 1;
        """
        return query


class StandardizingTextTransformation(Transformation):
    """A transformation class for standardizing the text case of a column in a table."""

    def get_query(self) -> str:
        """
            Constructs a SQL query to apply a text case transformation to the specified column.

            Raises:
                TransformationFailedException: If the column type is not 'STRING' or if
                there's no information about the field in the schema.

            Returns:
                str: The SQL query for applying the text case transformation.
            """
        convert_from = self.table.get_column_type(column_name=self.field)
        if not convert_from:
            raise TransformationFailedException(
                _("No data info for the field {field} in the schema.")
            ).format(field=self.field)
        if convert_from.upper() != "STRING":
            raise TransformationFailedException(_("Column must be of type string to apply text standardization."))

        text_case = self.options.get("text_case")
        query = f"""
            SELECT 
                * EXCEPT(`{self.field}`),
                {text_case}(`{self.field}`) AS `{self.field}`,
            FROM `{self.table.path}`;
        """
        return query
