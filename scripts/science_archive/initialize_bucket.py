import os
import requests
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
