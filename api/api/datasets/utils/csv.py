import csv
import math
from django.core.files.uploadedfile import TemporaryUploadedFile
import requests
import pandas as pd
from io import StringIO
from typing import Dict, List

from django.utils.translation import gettext_lazy as _

from .bigquery import is_valid_column_name, normalize_column_name
from .bigquery import normalize_column_name, get_bigquery_datatype
from api.datasets.exceptions import CsvPreviewFailed, InvalidCsvColumnException, InvalidFileException


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
        bigquery_type, mode = get_bigquery_datatype(df[column], pandas_type)

        result.append({
            "column_name": normalize_column_name(column) if skip_leading_rows > 0 else None,
            "data_type": bigquery_type,
            "mode": mode,
            "example_values": df[column][first_example_index:].head(5).fillna("").tolist()
        })
    return result


def create_dataframe_from_csv(file, sample: str = None) -> pd.DataFrame:
    """
        Creates a pandas DataFrame from a CSV file while detecting CSV parameters such as delimiter,
        quote character, and escape character.

        Args:
            file : The file containing the CSV data.
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


def get_content_from_url_csv(
        urls: list[str], 
        max_lines: int | None = 20, 
        skip_leading_rows: int = 1,
        **kwargs) -> str:
    """
    Get's the preview from a csv file url or list of urls
    validating column names and joining the files contents

    Returns:
        A string containing the first n lines from all given urls
        if max_lines is None return all the lines
    """

    assert len(urls) > 0, "It needs to be at least one url in the list"

    content = ""
    columns = pd.Index([])

    ml = None
    url_count = len(urls)
    if max_lines:
        ml = math.ceil(max_lines/url_count)

    for url in urls:
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            raise CsvPreviewFailed(detail=_("Invalid url or file/folder doesn't not exist"))

        line = 0
        cols = StringIO()
        for j in r.iter_lines():
            if line not in range(skip_leading_rows) or not content:
                content += j.decode() + "\r\n"

            if line == 0:
                cols.write(j.decode())

            line += 1
            if line == ml and max_lines:
                break

        cols.seek(0)
        df, csv_params = create_dataframe_from_csv(cols, sample=cols.getvalue())
        validate_csv_column_names(df)

        if columns.empty:
            columns = df.columns

        if not columns.equals(df.columns):
            raise CsvPreviewFailed(
                dict(detail=_("The tables need to have the same number of columns and column names"))
            )

    return content 


def validate_csv_column_names(df: pd.DataFrame, raise_exception=False) -> list:
    """
    Validates csv column names ensuring that it is compatible with
    google cloud directives
    """

    suffix_message = _("Column names must start with a letter and can only contain alphanumeric characters. Modify the column names in the source file or in the schema.")
    invalid_columns = [col for col in df.columns if not is_valid_column_name(col)]
    if invalid_columns and raise_exception:
        raise InvalidCsvColumnException(
            detail=_("Invalid column names in CSV:") + ', '.join(invalid_columns) + f". {suffix_message}"
        )

    return invalid_columns
