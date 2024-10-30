import json

import pandas as pd
from io import StringIO
from typing import Dict, List

from api.datasets.exceptions import InvalidFileException
from .bigquery import normalize_column_name, get_bigquery_datatype


def prepare_json_data_format(data: str, include_examples: bool = True) -> List:
    """Prepare JSON data schema to BigQuery format

    Args:
        data (str): JSON data
        include_examples (bool): If include examples

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

            column_data = {
                "column_name": normalize_column_name(column),
                "data_type": bigquery_type,
            }
            if include_examples:
                column_data["example_values"] = df[column].head(5).fillna("").tolist()

            if bigquery_type == "RECORD":
                nested_data = df[column].fillna("").tolist()
                nested_json = json.dumps(nested_data)
                column_data["fields"] = prepare_json_data_format(nested_json, include_examples=False)

            result.append(column_data)
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
