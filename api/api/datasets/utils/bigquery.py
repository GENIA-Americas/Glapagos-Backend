import re


def is_valid_column_name(column_name):
    """Validates if the column name follows BigQuery's naming rules."""
    if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]{0,127}$', column_name):
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
    normalized_name = re.sub(r'[^a-zA-Z0-9_]', '_', column_name)
    if normalized_name and normalized_name[0].isdigit():
        normalized_name = '_' + normalized_name
    return normalized_name[:128]