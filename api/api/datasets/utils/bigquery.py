import re
import unicodedata
import datetime
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
    1. Replaces accented characters (e.g., á, é) with their non-accented equivalents (e.g., a, e).
    2. Replaces 'ñ' with 'n'.
    3. Replaces any character that is not a letter (a-z, A-Z), digit (0-9), or underscore (_)
       with an underscore (_).
    4. Ensures that the resulting name does not start with a digit. If it does, an underscore
       is prepended to the name.
    5. Trims the resulting name to a maximum length of 128 characters.

    Args:
        column_name (str): The original column name to be normalized.

    Returns:
        str: The normalized column name that adheres to BigQuery's naming conventions.
    """
    # Replace accented characters with their unaccented equivalents
    normalized_name = unicodedata.normalize('NFD', column_name)
    normalized_name = ''.join(char for char in normalized_name if unicodedata.category(char) != 'Mn')

    # Replace 'ñ' with 'n'
    normalized_name = normalized_name.replace('ñ', 'n').replace('Ñ', 'N')

    # Replace invalid characters with an underscore
    normalized_name = re.sub(r'[^a-zA-Z0-9_]', '_', normalized_name)

    # Ensure the name does not start with a digit
    if normalized_name and normalized_name[0].isdigit():
        normalized_name = '_' + normalized_name

    # Trim the name to a maximum length of 128 characters
    return normalized_name[:128]


def get_bigquery_datatype(column: pd.Series, pandas_type: str) -> tuple[str, str]:
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
        dtype, mode = detect_object_type(column)
        if dtype:
            return dtype, mode
    return type_mapping.get(pandas_type.lower(), 'STRING'), "NULLABLE"


def detect_datetime(series):
    """
       Attempts to detect if a series contains datetime or date values.

       Args:
           series (pd.Series): Pandas Series to check.

       Returns:
           tuple(str, str): Data type, mode
    """
    mode = "NULLABLE"
    try:
        series = pd.to_datetime(series, errors='coerce')

        if series.notna().all():
            return 'DATETIME', mode
    except Exception:
        return None, None

    return None, None


def detect_time(series):
    """
    Attempts to detect if a series contains time values.

    Args:
        series (pd.Series): Pandas Series to check.

    Returns:
        tuple(str, str): Data type, mode
    """
    mode = "NULLABLE"
    try:
        series = pd.to_datetime(series, format='%H:%M:%S', errors='coerce').dt.time

        if not series.isna().all():
            if series.notna().all():
                return 'TIME', mode
    except Exception:
        return None, None

    return None, None


def detect_element_type_in_array_bigquery(series):
    """
    Detects the BigQuery-compatible data type of elements within lists in a Pandas series.

    Args:
        series (pd.Series): Pandas Series to check.

    Returns:
        tuple(str, str): Data type, mode
    """
    mode = "REPEATED"
    python_to_bigquery_type = {
        int: "INT64",
        float: "FLOAT64",
        str: "STRING",
        bool: "BOOLEAN",
        datetime.datetime: "DATETIME",
        datetime.date: "DATE",
        datetime.time: "TIME",
        pd.Timestamp: "DATETIME",
    }

    non_empty_lists = [value for value in series if isinstance(value, list) and value]

    if not non_empty_lists:
        return None, None

    first_element_type = type(non_empty_lists[0][0])

    if all(isinstance(item, int) for value in non_empty_lists for item in value):
        return "INT64", mode
    elif all(isinstance(item, (int, float)) for value in non_empty_lists for item in value):
        return "FLOAT64", mode
    elif all(isinstance(item, first_element_type) for value in non_empty_lists for item in value):
        return python_to_bigquery_type.get(first_element_type, "STRING"), mode

    return None, None


def detect_struct(series: pd.Series):
    """
    Detects if a pandas Series contains dictionary-like entries, suggesting a STRUCT type.

    Args:
        series (pd.Series): The pandas Series to be analyzed.

    Returns:
         tuple(str, str): Data type, mode
    """
    mode = "NULLABLE"
    if all(isinstance(item, dict) for item in series.dropna()):
        return 'RECORD', mode

    return None, None


def detect_object_type(series: pd.Series) -> tuple[str, str]:
    """
    Determines the type of data in a pandas Series when the dtype is 'object'.

    This function attempts to identify whether the series contains time values,
    datetime values, or list values. The detection is performed in order of
    precedence: TIME, DATETIME, and ARRAY.

    Args:
        series (pd.Series): The pandas Series to be analyzed.

    Returns:
        tuple(str, str): Data type, mode.
    """
    detection_functions = [
        detect_time,
        detect_datetime,
        detect_element_type_in_array_bigquery,
        detect_struct,
    ]

    for detect in detection_functions:
        detected_type, mode = detect(series)
        if detected_type:
            return detected_type, mode

    return None, None
