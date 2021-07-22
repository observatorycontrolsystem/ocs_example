
import os
import requests

################################################################################
# The following environment variables are required by the ingester.
# If running in the archive container, the values should already be loaded from 
# the compose file.
# Otherwise, uncomment the code below to manually define the environment values.
# Ingester docs: https://ingester.readthedocs.io/en/latest/README.html
################################################################################

# AWS keys can be found in the docker compose file, defined in the minio instances.
#os.environ['AWS_ACCESS_KEY_ID'] = 'minio_access_key'
#os.environ['AWS_SECRET_ACCESS_KEY'] = 'minio_secret'
#os.environ['AWS_DEFAULT_REGION'] = 'minio_region'
#os.environ['BUCKET'] = 'ocs-example-bucket'

# This is the url pointing to the minio bucket. 
# For a bucket in AWS, the endpoint would follow the convention 
# of http://s3.<region-name>.amazonaws.com
#os.environ['S3_ENDPOINT_URL'] = 'http://localhost:9000/'

# This is the science archive api endpoint
#os.environ['API_ROOT'] = 'http://localhost:9500/'

# Test mode disables the opentsdb metrics reporting, which is not included 
# in the ocs_example stack.
#os.environ['OPENTSDB_PYTHON_METRICS_TEST_MODE'] = 'True'


################################################################################
# Get the archive token for the ingester with the username and password 
# defined in the science archive service in the docker compose file. 
################################################################################
username = 'test_user'
password = 'test_pass'
admin_archive_token = requests.post(
    'http://localhost:9500/api-token-auth/',
    data = {
        'username': username,
        'password': password
    }
).json().get('token')
# Set as an environment variable so the ingester can use it.
os.environ['AUTH_TOKEN'] = admin_archive_token


################################################################################
# Import the ingester only after the required environment variables have been set.
################################################################################
from ocs_ingester import ingester


################################################################################
# Now that the environment is configured properly, we can begin the ingesting routine.
################################################################################

# Specify the path of the file to ingest.
test_file_path = '/example_data/ogg0m406-kb27-20210720-0305-s91.fits.fz'

with open(test_file_path, 'rb') as fileobj:
    if not ingester.frame_exists(fileobj):
        print("Adding file to the archive.")
        record = ingester.validate_fits_and_create_archive_record(fileobj)

        # Upload the file to our bucket
        s3_version = ingester.upload_file_to_s3(fileobj)

        # Change the version key to be compatible with the ingester (32 char max)
        # This step is only necessary when using minio. With a real S3 bucket, the 
        # upload response should return a version key that doesn't need to be modified. 
        s3_version['key'] = s3_version['key'].replace('-', '')

        # Save the record in the archive db, which makes it appear in the archive api
        ingested_record = ingester.ingest_archive_record(s3_version, record)
    else:
        print("File already exists in the archive, nothing uploaded.")
