import csv
import pandas as pd
from io import StringIO
from typing import Dict, List


def csv_parameters_detect(sample: str) -> Dict:
    """Detects format parameters of a given csv

    Args:
        sample (str): CSV data sample

    Returns:
        (Dict): CSV data params

    """
    sniffer = csv.Sniffer()

    dialect = sniffer.sniff(sample)

    has_header = sniffer.has_header(sample)

    return {
        'delimiter': dialect.delimiter,
        'quotechar': dialect.quotechar,
        'escapechar': dialect.escapechar,
        'doublequote': dialect.doublequote,
        'skipinitialspace': dialect.skipinitialspace,
        'lineterminator': dialect.lineterminator,
        'quoting': dialect.quoting,
        'has_header': has_header
    }


def detect_datetime(series):
    """
       Attempts to detect if a series contains datetime or date values.

       Args:
           series (pd.Series): Pandas Series to check.

       Returns:
           str: Detected data type ('DATETIME', 'DATA' or None).
    """
    try:
        series = pd.to_datetime(series, errors='coerce')

        if series.notna().all():
            if (series.dt.time == pd.Timestamp('00:00:00').time()).all():
                return 'DATE'
            else:
                return 'DATETIME'
    except (ValueError, TypeError):
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
    except (ValueError, TypeError):
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


def prepare_csv_data_format(data: str) -> List:
    """Prepare csv data schema to Big Query format

    Args:
        data (str): CSV data

    Returns:
        (List): CSV rows in Big Query format

    """
    csv_file = StringIO(data)
    csv_params = csv_parameters_detect(data)
    df = pd.read_csv(
        csv_file,
        sep=csv_params['delimiter'],
        quotechar=csv_params['quotechar'],
        escapechar=csv_params['escapechar'],
    )

    result = []
    for column in df.columns:
        pandas_type = str(df[column].dtype)
        bigquery_type = get_bigquery_datatype(df[column], pandas_type)

        result.append({
            "column_name": column if csv_params['has_header'] else None,
            "data_type": bigquery_type,
            "example_values": df[column].head(5).tolist()
        })
    return result

