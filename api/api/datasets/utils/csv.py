import csv
import pandas as pd
from io import StringIO
from typing import Dict, List

from .bigquery import normalize_column_name
from api.datasets.exceptions import InvalidFileException


def csv_parameters_detect(sample: str) -> Dict:
    """Detects format parameters of a given CSV.

    Args:
        sample (str): CSV data sample

    Returns:
        (Dict): CSV data params or defaults if detection fails.
    """
    sniffer = csv.Sniffer()

    try:
        dialect = sniffer.sniff(sample)
    except csv.Error:
        return {
            'delimiter': ',',
            'quotechar': '"',
            'escapechar': None,
            'doublequote': True,
            'skipinitialspace': False,
            'lineterminator': '\n',
            'quoting': csv.QUOTE_MINIMAL,
        }

    return {
        'delimiter': dialect.delimiter,
        'quotechar': dialect.quotechar,
        'escapechar': dialect.escapechar,
        'doublequote': dialect.doublequote,
        'skipinitialspace': dialect.skipinitialspace,
        'lineterminator': dialect.lineterminator,
        'quoting': dialect.quoting,
    }


def detect_datetime(series):
    """
       Attempts to detect if a series contains datetime or date values.

       Args:
           series (pd.Series): Pandas Series to check.

       Returns:
           str: Detected data type ('DATETIME' or None).
    """
    try:
        series = pd.to_datetime(series, errors='coerce')

        if series.notna().all():
            return 'DATETIME'
    except Exception:
        return None

    return None


def detect_time(series):
    """
    Attempts to detect if a series contains time values.

    Args:
        series (pd.Series): Pandas Series to check.

    Returns:
        str: Detected data type ('TIME' or None).
    """
    try:
        series = pd.to_datetime(series, format='%H:%M:%S', errors='coerce').dt.time

        if not series.isna().all():
            if series.notna().all():
                return 'TIME'
    except Exception:
        return None

    return None


def detect_object_type(series: pd.Series) -> str:
    """
        Determines the type of data in a pandas Series when the dtype is 'object'.

        This function attempts to identify whether the series contains time values or
        datetime values. It first checks for time values and if not found, it checks
        for datetime values.

        Args:
            series (pd.Series): The pandas Series to be analyzed.

        Returns:
            str: The detected data type ('TIME', 'DATE', 'DATETIME', or None).
        """
    dtype = detect_time(series)
    if dtype is None:
        dtype = detect_datetime(series)
    return dtype


def get_bigquery_datatype(column: pd.Series, pandas_type: str) -> str:
    """
       Maps pandas data types to BigQuery data types.

       This function converts a pandas data type into its corresponding BigQuery data type.
       If the pandas type is 'object', it further determines if the column contains time or
       datetime values. The mapping is based on predefined rules and type detection.

       Args:
           column (pd.Series): The pandas Series representing the column data.
           pandas_type (str): The data type of the pandas column as a string.

       Returns:
           str: The corresponding BigQuery data type.
       """
    type_mapping = {
        'int64': 'INT64',
        'float64': 'FLOAT64',
        'object': 'STRING',
        'string': 'STRING',
        'bool': 'BOOLEAN',
        'datetime64[ns]': 'DATETIME',
        'datetime64': 'DATETIME',
        'timedelta[ns]': 'TIME',
        'timedelta': 'TIME',
    }

    if pandas_type == 'object':
        dtype = detect_object_type(column)
        if dtype:
            return dtype
    return type_mapping.get(pandas_type.lower(), 'STRING')


def prepare_csv_data_format(data: str, skip_leading_rows: int) -> List:
    """Prepare csv data schema to Big Query format

    Args:
        data (str): CSV data
        skip_leading_rows (int): Headers rows

    Returns:
        (List): CSV rows in Big Query format

    """
    csv_file = StringIO(data)
    df, csv_params = create_dataframe_from_csv(csv_file, data)

    first_example_index = max(skip_leading_rows - 1, 0)
    result = []
    for column in df.columns:
        pandas_type = str(df[column].dtype)
        bigquery_type = get_bigquery_datatype(df[column], pandas_type)

        result.append({
            "column_name": normalize_column_name(column) if skip_leading_rows > 0 else None,
            "data_type": bigquery_type,
            "example_values": df[column][first_example_index:].head(5).fillna("").tolist()
        })
    return result


def create_dataframe_from_csv(file, sample: str = None) -> pd.DataFrame:
    """
        Creates a pandas DataFrame from a CSV file while detecting CSV parameters such as delimiter,
        quote character, and escape character.

        Args:
            file : The file containing the CSV data.
            skip_leading_rows (int): Number of rows to skip at the beginning of the file.
            sample : (str): A sample string from the file used to detect CSV parameters.

        Returns:
            df (pd.DataFrame): The DataFrame created from the CSV file.
            csv_params (dict) A dictionary containing the detected CSV parameters
    """
    try:
        if not sample:
            sample = file.read(4096).decode('utf-8')
        file.seek(0)
        csv_params = csv_parameters_detect(sample)

        df = pd.read_csv(
            file,
            sep=csv_params['delimiter'],
            quotechar=csv_params['quotechar'],
            escapechar=csv_params['escapechar'],
            skipinitialspace=csv_params['skipinitialspace'],
        )
        file.seek(0)

        return df, csv_params
    except Exception as exp:
        raise InvalidFileException(error=str(exp))
