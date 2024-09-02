from google.cloud import storage

def upload_to_gcs(file, bucket_name, destination_blob_name):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(file, content_type=file.content_type)
    return blob.public_url
