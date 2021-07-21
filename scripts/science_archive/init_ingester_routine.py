import os
from ocs_ingester import ingester
import boto3

session = boto3.Session()

# create a bucket
try:
    client = session.client('s3', endpoint_url=os.getenv('S3_ENDPOINT_URL'))
    bucket = client.create_bucket(
        Bucket=os.getenv('AWS_BUCKET'),
    )
    print(bucket)
except:
    print('bucket already exists')

# enable versioning
try:
    resource = session.resource('s3', endpoint_url=os.getenv('S3_ENDPOINT_URL'))
    bucket = resource.Bucket(os.getenv('AWS_BUCKET'))
    bucket.Versioning().enable()
    print("Enabled versioning on bucket %s.", bucket.name)
except:
    print("Couldn't enable versioning on bucket")

# ingest an example frame
with open('/example_data/ogg0m406-kb27-20210720-0307-s91.fits.fz', 'rb') as fileobj:
    if not ingester.frame_exists(fileobj):
        record = ingester.validate_fits_and_create_archive_record(fileobj)
        s3_version = ingester.upload_file_to_s3(fileobj)
        # Change the version key to be compatible with the ingester (32 char max)
        s3_version['key'] = s3_version['key'].replace('-', '')
        ingested_record = ingester.ingest_archive_record(s3_version, record)
