import os
import shutil
from astropy.io import fits
import requests
import urllib
import time
from pprint import pprint

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
#os.environ['AWS_DEFAULT_REGION'] = 'minio-region'
#os.environ['BUCKET'] = 'ocs-example-bucket'

# This is the url pointing to the minio bucket. 
# For a bucket in AWS, the endpoint would follow the convention 
# of http://s3.<region-name>.amazonaws.com
#os.environ['S3_ENDPOINT_URL'] = 'http://localhost:9000/'

# This is the science archive api endpoint
#os.environ['API_ROOT'] = 'http://localhost:9500/'

# This is the base url for the observation portal, used to fetch observations
#os.environ['OBSERVATION_PORTAL_BASE_URL'] = 'http://localhost:8000/api'

# Test mode disables the opentsdb metrics reporting, which is not included 
# in the ocs_example stack.
#os.environ['OPENTSDB_PYTHON_METRICS_TEST_MODE'] = 'True'


################################################################################
# Get the auth token for science archive which is used by the ingester, 
# and the auth token for the obs portal used to get completed observations.
################################################################################

# SCIENCE ARCHIVE TOKEN
# These credentials are defined in the science_archive startup command in the 
# docker compose file when creating the archive user
archive_username = 'test_user'
archive_password = 'test_pass'

# Trade a username/password for a token granting science_archive upload permissions
admin_archive_token = requests.post(
    'http://localhost:9500/api-token-auth/',
    data = {
        'username': archive_username,
        'password': archive_password
    }
).json().get('token')

# Set as an environment variable so the ingester can use it.
# This must happen before importing the ingester library.
os.environ['AUTH_TOKEN'] = admin_archive_token
print(os.getenv('AUTH_TOKEN'))

# OBSERVATION PORTAL TOKEN
# First, make sure the observation portal is accepting connections before we query it.
obs_portal_ready = False
while not obs_portal_ready:
    try:
        requests.get('http://observation-portal:8000/api/').text  # try connecting
        obs_portal_ready = True
    except Exception as e:
        print("...waiting for the observation portal to come online...")
        time.sleep(1)
    
# These credentials are defined in the observation-portal startup command in the 
# docker compose file, during user creation.
obs_portal_username = 'test_user'
obs_portal_password = 'test_pass'

# Trade the username/password for a token granting access to completed observations
observations_token_endpoint = os.environ['OBSERVATION_PORTAL_BASE_URL'] + '/api-token-auth/'
observations_token = requests.post(
    observations_token_endpoint,
    data = {
        'username': obs_portal_username,
        'password': obs_portal_password
    }
).json().get('token')


################################################################################
# Import the ingester only after the needed environment variables have been set.
################################################################################
from ocs_ingester import ingester


################################################################################
# Create a temporary directory for working with our fits file.
# The goal is to run a loop that modifies our sample data's metadata to match
# a completed observation, and then upload that file. 
################################################################################

# Make a temporary directory
tmp_fits_dir =  f'/example_data/tmp_fits'
try:
    os.makedirs(tmp_fits_dir)
except OSError:
    print('Could not create the directory ', tmp_fits_dir)
    pass

# copy the fits file so that we can modify it without changing the original
file = 'ogg0m406-kb27-20210720-0305-s91.fits.fz'
original_fits_path = f'/example_data/{file}'
copied_fits_path = f'/example_data/tmp_fits/{file}'
shutil.copyfile(original_fits_path, copied_fits_path)
filename_counter = -1

################################################################################
# Helpers to get completed observations so we can make matching data files
################################################################################
def get_completed_observations():
    observations_endpoint = f"{os.getenv('OBSERVATION_PORTAL_BASE_URL')}/observations"
    query_params = {
        "state": "COMPLETED",
        "user": "test_user",
    }
    observations_endpoint += "?" + urllib.parse.urlencode(query_params)
    obs_auth_header = { "Authorization": f"Token {observations_token}" }

    observations = requests.get(observations_endpoint, headers=obs_auth_header).json()
    pprint(len(observations["results"]))
    return observations["results"]

def header_vals_from_observation(obs):
    return {
        #"RLEVEL": "",
        "DAY_OBS": obs['end'].split('T')[0],
        "DATE_OBS": obs['end'],
        "PROPID": obs['proposal'],
        "INSTRUME": obs['request']['configurations'][0]['instrument_name'],
        "OBJECT": obs['request']['configurations'][0]['target']['name'],
        "SITEID": obs['site'],
        "TELID": obs['telescope'],
        "EXPTIME": obs['request']['configurations'][0]['instrument_configs'][0]['exposure_time'],
        "FILTER": obs['request']['configurations'][0]['instrument_configs'][0]['optical_elements']['filter'],
        "OBSTYPE": obs['request']['configurations'][0]['type'],
        "BLKUID": obs['id'],
        "REQNUM": obs['request']['configurations'][0]['id'],
        "TELID": obs['telescope'],
    }

def filename_from_observation_header_vals(header_vals):
    filename = f"{header_vals['SITEID']}{header_vals['TELID']}"
    filename += f"-{header_vals['INSTRUME']}-{header_vals['DAY_OBS'].replace('-', '')}"
    filename += f"-{str(filename_counter).zfill(4)}-e91.fits.fz"
    return filename


################################################################################
# Iterate through completed observations and upload a matching sample fits file. 
################################################################################
for obs in get_completed_observations():

    filename_counter += 1  # get a unique number for the filename
    
    # Open our fits file to modify the headers. 
    # This is used by the ingester when writing the file attributes. 
    with fits.open(copied_fits_path, mode='update') as fits_copy:

        # Gather the observation values to put in the header
        header_vals = header_vals_from_observation(obs)
        header = fits_copy[1].header

        # Add header values we obtained from the completed observation we want to match.
        for key, val in header_vals.items():
            header.set(key, val)

        # Remove any headers that would count towards 'related frames' since 
        # we shouldn't have any for our synthetic data
        related_frame_keys = [
            'L1IDBIAS', 'L1IDDARK', 'L1IDFLAT', 'L1IDSHUT',
            'L1IDMASK', 'L1IDFRNG', 'L1IDCAT', 'L1IDARC',
            'L1ID1D', 'L1ID2D', 'L1IDSUM', 'TARFILE',
            'ORIGNAME', 'ARCFILE', 'FLATFILE', 'GUIDETAR',
        ]
        for key in related_frame_keys:
            header.set(key, '')
    # Python's context manager automatically saves file changes to disk.
    
    # Rename the copy of our fits file 
    # This is to provide a correct and unique filename for the ingester to use. 
    filename = filename_from_observation_header_vals(header_vals)
    renamed_copied_fits_path = f"/example_data/tmp_fits/{filename}"
    os.rename(copied_fits_path, renamed_copied_fits_path)
    copied_fits_path = renamed_copied_fits_path

    # Ingest frame
    with open(copied_fits_path, 'rb') as fileobj:
        if not ingester.frame_exists(fileobj):
            print(f"Adding file {filename} to the archive.")
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

# Finally, remove our temporary directory
shutil.rmtree(tmp_fits_dir)