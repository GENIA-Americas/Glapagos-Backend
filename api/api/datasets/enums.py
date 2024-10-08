from enum import Enum

from django.db import models


class FileType(models.TextChoices):
    CSV = 'csv', 'CSV'
    JSON = 'json', 'JSON'
    TXT = 'txt', 'TXT'


class TransformationOption(Enum):
    MISSING_VALUES = "MissingValues"
    DATA_TYPE_CONVERSION = "DataTypeConversion"
    REMOVE_DUPLICATES = "RemoveDuplicates"
