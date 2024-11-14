import json
from django.core.files.uploadedfile import TemporaryUploadedFile
import requests
import math

import pandas as pd
from io import StringIO
from typing import Dict, List

from django.utils.translation import gettext_lazy as _

from api.datasets.exceptions import InvalidFileException, JsonPreviewFailed
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
        data_obj = json.loads(data)
        while isinstance(data_obj, str):
            data_obj = json.loads(data_obj)
        data_obj = [data_obj] if isinstance(data_obj, dict) else data_obj
        data = json.dumps(data_obj)

        json_data = StringIO(data)
        df = pd.read_json(json_data)
        result = []
        for column in df.columns:
            pandas_type = str(df[column].dtype)
            bigquery_type, mode = get_bigquery_datatype(df[column], pandas_type)

            column_data = {
                "column_name": normalize_column_name(column),
                "data_type": bigquery_type,
                "mode": mode,
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
        raise exp
        raise InvalidFileException(error=str(exp))


def create_dataframe_from_json(file) -> pd.DataFrame:
    """
        Creates a pandas DataFrame from a JSON file.

        Args:
            file: The file containing the JSON data.

        Returns:
            df (pd.DataFrame): The DataFrame created from the JSON file.
    """
    content = file.read().decode('utf-8')
    file.seek(0)
    try:
        data = json.loads(content)
        if isinstance(data, list):
            df = pd.DataFrame(data)
            return df
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
            return df
    except Exception:
        pass

    try:
        df = pd.read_json(content, lines=True)
        return df
    except Exception as exp:
        raise InvalidFileException(error=str(exp))


def get_content_from_url_json(
        urls: list[str], 
        max_lines: int | None  = 20,
        **kwargs) -> str:
    """
    Get's the preview from a json file url or list of urls
    validating column names and joining the file contents

    Returns:
        A string containing the first n lines from all given urls
    """

    assert len(urls) > 0, "It needs to be at least one url in the list"

    ml = 0 
    url_count = len(urls)
    if max_lines:
        ml = math.ceil(max_lines/url_count)

    columns = None 
    items = []
    item_count = 0

    for url in urls:
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            raise JsonPreviewFailed(detail=_("Invalid url or file/folder doesn't not exist"))

        open_brackets = 0
        item = ""
        save = False
        complete_item = False
        for chunck in r.iter_content(chunk_size=1024):
            for c in chunck.decode():
                if c == "{":
                    save = True
                    open_brackets += 1
                elif c == "}": 
                    open_brackets -= 1
                    if open_brackets == 0:
                        complete_item = True

                if save:
                    item += c

                if complete_item:
                    if item[0] in [",", "["]: 
                        item = item[1:]

                    load_item = json.loads(item)
                    items.append(load_item)
                    item_count += 1

                    item = ""
                    save = False
                    complete_item = False

                    if columns == None:
                        columns = load_item.keys() 

                    if columns != load_item.keys():
                        raise JsonPreviewFailed(
                            dict(detail=_("The tables need to have the same number of columns and column names"))
                        )

                if item_count == ml and max_lines:
                    break

            if len(items) == max_lines and max_lines:
                break

    return json.dumps(items)

