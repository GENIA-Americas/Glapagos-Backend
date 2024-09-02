from django.db import models

class FileType(models.TextChoices):
    CSV = 'csv', 'CSV'
    JSON = 'json', 'JSON'
    TXT = 'txt', 'TXT'
