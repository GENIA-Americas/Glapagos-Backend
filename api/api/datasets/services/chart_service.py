from abc import ABC, abstractmethod
from typing import List

from api.datasets.exceptions import ChartLimitExceededException
from api.datasets.models import Table
from api.datasets.services import BigQueryService
from api.users.models import User


class ChartService(ABC):
    """Abstract base class for chart services."""
    def __init__(self, table: Table, user: User, limit: int) -> None:
        """
            Initializes the ChartService with a table, user, and result limit.

            Args:
                table (Table): The table containing data for the chart.
                user (User): The user requesting the chart data.
                limit (int): The maximum number of results to process.
        """
        self.table = table
        self.user = user
        self.limit = limit

    @abstractmethod
    def get_query(self) -> str:
        """
           Generates the SQL query string to be executed.

           Returns:
               str: The SQL query string.
       """
        ...

    @abstractmethod
    def process(self) -> List:
        """
            Processes the query results and returns them as a list.

            Returns:
                List: A list containing the processed results.
        """
        ...


class CategoryChartService(ChartService):
    """Service for generating category-based charts."""
    def __init__(self, table: Table, user: User, limit: int, category: str, axis: str) -> None:
        """
            Initializes the CategoryChartService with the table, user, limit, category, and axis.

            Args:
                table (Table): The table containing data for the chart.
                user (User): The user requesting the chart data.
                limit (int): The maximum number of results to process.
                category (str): The column name to group by.
                axis (str): The axis ('x' or 'y') for the category data.
        """
        super().__init__(table, user, limit)
        self.category = category
        self.category_axis = axis
        self.count_axis = 'y' if axis == 'x' else 'x'

    def get_query(self) -> str:
        """
            Constructs the SQL query for counting occurrences of the specified category.

            Returns:
                str: The SQL query string.
        """
        query = f"""
            SELECT 
                `{self.category}` AS `{self.category_axis}`, 
                COUNT(*) AS `{self.count_axis}`
            FROM `{self.table.path}`
            GROUP BY `{self.category}`
        """
        return query

    def process(self) -> List:
        """
            Executes the query and processes the results.

            Returns:
                List: A list of dictionaries with category and count data.

            Raises:
                ChartLimitExceededException: If the number of rows exceeds the specified limit.
        """
        query = self.get_query()
        bigquery_client = BigQueryService(user=self.user)
        query_results = bigquery_client.query(query)
        if query_results.total_rows > self.limit > 0:
            raise ChartLimitExceededException()

        results = []

        for row in query_results:
            results.append({
                self.category_axis: row[self.category_axis],
                self.count_axis: row[self.count_axis]
            })

        return results


def chart_select(x: str, y: str, table: Table, user: User, limit: int = 0) -> ChartService:
    """
        Selects and returns the appropriate ChartService based on the provided parameters.

        Args:
            x (str): The column name for the x-axis.
            y (str): The column name for the y-axis.
            table (Table): The table containing data for the chart.
            user (User): The user requesting the chart data.
            limit (int): The maximum number of results to process.

        Returns:
            ChartService: An instance of CategoryChartService.
        """
    if not x or not y:
        category = x or y
        axis = 'x' if not y else 'y'
        return CategoryChartService(table, user, limit, category, axis)
