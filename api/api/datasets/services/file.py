from google.cloud import storage
from google.cloud import bigquery
from django.conf import settings
from api.datasets.models import Table


def upload_to_gcs(file, bucket_name, destination_blob_name):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file, content_type=file.content_type)
    return blob.public_url


def get_source_format(extension):
    """Returns the BigQuery SourceFormat based on file extension."""
    formats = {
        "csv": bigquery.SourceFormat.CSV,
        "json": bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    }
    return formats.get(extension, bigquery.SourceFormat.CSV)


def mount_file_in_bq(table: Table):
    client = bigquery.Client()

    dataset_ref = bigquery.DatasetReference(settings.BQ_PROJECT_ID, table.dataset_name)
    dataset = client.get_dataset(dataset_ref)
    table_ref = dataset.table(table.name)
    extension = table.file.type

    job_config = bigquery.LoadJobConfig(
        source_format=get_source_format(extension),
        autodetect=True,
        skip_leading_rows=1,
    )

    gcs_uri = table.file.storage_url

    load_job = client.load_table_from_uri(
        gcs_uri, table_ref, job_config=job_config
    )

    load_job.result()
    table_bq = client.get_table(table_ref)
    table.mounted = True
    table.data_expiration = table_bq.expires
    table.number_of_rows = table_bq.num_rows
    table.total_logical_bytes = table_bq.num_bytes
    table.save()