from enum import Enum

from django.db import models

class UploadType(models.TextChoices):
    FILE = 'file', 'FILE'
    URL = 'url', 'URL'

class FileType(models.TextChoices):
    CSV = 'csv', 'CSV'
    JSON = 'json', 'JSON'
    JSONL = 'jsonl', 'JSONL'
    TXT = 'txt', 'TXT'


class TransformationOption(Enum):
    MISSING_VALUES = "MissingValues"
    DATA_TYPE_CONVERSION = "DataTypeConversion"
    REMOVE_DUPLICATES = "RemoveDuplicates"
    STANDARDIZING_TEXT = "StandardizingText"
