import re
import pandas as pd


def is_valid_column_name(column_name):
    """Validates if the column name follows BigQuery's naming rules."""
    if re.match(r'^[a-zA-Z_áéíóúÁÉÍÓÚñÑ][a-zA-Z0-9_áéíóúÁÉÍÓÚñÑ]{0,127}$', column_name):
        return True
    return False


def normalize_column_name(column_name):
    """
    Normalize a column name to make it compatible with BigQuery.

    This function applies the following transformations to the input column name:
    1. Replaces any character that is not a letter (a-z, A-Z), digit (0-9), or underscore (_)
       with an underscore (_).
    2. Ensures that the resulting name does not start with a digit. If it does, an underscore
       is prepended to the name.
    3. Trims the resulting name to a maximum length of 128 characters.

    Args:
        column_name (str): The original column name to be normalized.

    Returns:
        str: The normalized column name that adheres to BigQuery's naming conventions.
    """
    normalized_name = re.sub(r'[^a-zA-Z0-9_áéíóúÁÉÍÓÚñÑ]', '_', column_name)
    if normalized_name and normalized_name[0].isdigit():
        normalized_name = '_' + normalized_name
    return normalized_name[:128]


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


def detect_list(series):
    """
    Attempts to detect if a series contains list values.

    Args:
        series (pd.Series): Pandas Series to check.

    Returns:
        str: Detected data type ('ARRAY' or None).
    """
    # Check if all values in the series are lists
    if all(isinstance(value, list) for value in series):
        return 'ARRAY'

    return None


def detect_struct(series: pd.Series):
    """
    Detects if a pandas Series contains dictionary-like entries, suggesting a STRUCT type.

    Args:
        series (pd.Series): The pandas Series to be analyzed.

    Returns:
        str: 'STRUCT' if dictionary-like entries are found, otherwise None.
    """
    if all(isinstance(item, dict) for item in series.dropna()):
        return 'RECORD'

    return None


def detect_object_type(series: pd.Series) -> str:
    """
    Determines the type of data in a pandas Series when the dtype is 'object'.

    This function attempts to identify whether the series contains time values,
    datetime values, or list values. The detection is performed in order of
    precedence: TIME, DATETIME, and ARRAY.

    Args:
        series (pd.Series): The pandas Series to be analyzed.

    Returns:
        str: The detected data type ('TIME', 'DATETIME', 'ARRAY', or None).
    """
    detection_functions = [
        detect_time,
        detect_datetime,
        detect_list,
        detect_struct,
    ]

    for detect in detection_functions:
        detected_type = detect(series)
        if detected_type:
            return detected_type
