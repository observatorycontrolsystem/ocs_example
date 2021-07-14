import os
from ocs_ingester import ingester
import boto3

print('running in the init_ingester_routine')
print('archive access token: ', os.getenv('AUTH_TOKEN'))

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
    print("Couldn't enable versioning on bucket %s.", bucket.name)

# ingest a frame
with open('/fits/cpt1m012-fa06-20210705-0237-e91.fits.fz', 'rb') as fileobj:
    ingested_record = ingester.upload_file_and_ingest_to_archive(fileobj)
    print('ingested record: ')
    print(ingested_record)
