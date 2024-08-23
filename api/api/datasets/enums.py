from django.db import models

class DatasetType(models.TextChoices):
    CSV = 'csv', 'CSV'
    JSON = 'json', 'JSON'
    TXT = 'txt', 'TXT'
