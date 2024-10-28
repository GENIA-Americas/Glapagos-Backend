import pandas as pd
from io import StringIO
from typing import Dict, List

from api.datasets.exceptions import InvalidFileException
from .bigquery import normalize_column_name, get_bigquery_datatype


def prepare_json_data_format(data: str) -> List:
    """Prepare JSON data schema to BigQuery format

    Args:
        data (str): JSON data

    Returns:
        (List): JSON rows in BigQuery format
    """
    try:
        json_data = StringIO(data)
        df = pd.read_json(json_data)

        result = []
        for column in df.columns:
            pandas_type = str(df[column].dtype)
            bigquery_type = get_bigquery_datatype(df[column], pandas_type)

            result.append({
                "column_name": normalize_column_name(column),
                "data_type": bigquery_type,
                "example_values": df[column].head(5).fillna("").tolist()
            })
        return result
    except Exception as exp:
        raise InvalidFileException(error=str(exp))


def create_dataframe_from_json(file) -> pd.DataFrame:
    """
        Creates a pandas DataFrame from a JSON file.

        Args:
            file: The file containing the JSON data.

        Returns:
            df (pd.DataFrame): The DataFrame created from the JSON file.
    """
    try:
        df = pd.read_json(file)
        return df
    except Exception as exp:
        raise InvalidFileException(error=str(exp))
