# OCS Example Project

## A pre-populated demo of the OCS services

This example project provides a docker-compose file which launches 
an [Observation Portal](https://github.com/observatorycontrolsystem/observation-portal), 
a [web interface](https://github.com/observatorycontrolsystem/ocs-example-frontend) for the observation portal, 
a [Configuration Database](https://github.com/observatorycontrolsystem/configdb), 
a [Downtime Database](https://github.com/observatorycontrolsystem/downtime), 
a [Science Archive](https://github.com/observatorycontrolsystem/science-archive), 
and an [Adaptive Scheduler](https://github.com/observatorycontrolsystem/adaptive_scheduler), 
all connected together with pre-populated sample data.

## Credentials

By default, the Observation Portal will have a single account created with the username `test_user` and the password `test_pass`. This can be used to login to the Observation Portal, Science Archive, or the admin interface of the Configuration or Downtime Databases.

## Example Data

A number of management scripts are run on container startup to pre-populate the database with some example data. Note that these scripts run on startup to provide an initial set of test data to allow you start playing around with the OCS projects, however generally the API endpoints or the admin site of each project should be used to update/ add data in a running project.

### Configuration Database

* `init_e2e_data` - This command creates a site, enclosure, telescope, camera, and instrument with a few filters and a readout mode. This should be the minimum information necessary to submit a request.

### Downtime Database

* `create_downtime` - This command creates a downtime on a given site, enclosure, and telescope at a given time, for a given reason. This is a called by the docker-compose file to set up a downtime in the past and in the future.

### Observation Portal

* `create_application` - This command creates an OAauth application link in the project which gives that application the ability to authenticate off of the oauth backend.
* `create_user` - This command creates a superuser account and associated Profile, and creates an associated API Token.
* `create_semester` - This command creates a Semester with the given id, start, and end times, which default around the present time.
* `create_proposal` - This command creates a proposal with the specified properties, assigns the given user as the proposal PI, and optionally creates time allocations with 100 hours of all types of observing time on all schedulable instruments for the current Semester. There must be an existing, current semester defined to be able to create time allocations for the proposal.
* `example_requests` - This command creates a set of RequestGroups with different observation types and states, and a set of associated Observations for the Requests that should have been attempted. It requires that a valid User and Proposal be passed in. Requests are created both in the past and in the future of the current time. Targets are choosen randomly out of a predefined list if they are visible given the defined sites in Configdb.

## Running the example

First, you must ensure that you pulled down the submodule `docker-postgresql-multiple-databases`. This can be done when cloning the repo by adding `--recurse-submodules --remote-submodules` to your `git clone` command:

```
git clone git@github.com:observatorycontrolsystem/ocs_example.git --recurse-submodules --remote-submodules
```

It could also be done after cloning the base repo by running `git submodule init` followed by `git submodule update` in the base repo directory:

```
git clone git@github.com:observatorycontrolsystem/ocs_example.git
cd ocs_example
git submodule init
git submodule update
```

After doing either of these, your `docker-postgresql-multiple-databases` directory should contain a file named `create-multiple-postgresql-databases.sh`, which is used to create multiple databases in the same postgresql container. 

This example requires access to the observatory control system docker images, which are all on [Docker Hub](https://hub.docker.com/u/observatorycontrolsystem). It also requires your system to be running docker and have docker-compose installed. To run the example applications, run:


```docker-compose up -d```

from within this directory. Once running, you can use the [credentials given above](https://github.com/observatorycontrolsystem/ocs_example#credentials) to access the admin interface of any of the applications, or to login and view/submit requests on the Observation Portal's web interface.

By default, the docker-compose file has ports set up such that:

* The **Observation Portal** API is accessible from <http://127.0.0.1:8000/api/>, and its admin interface is accessible from <http://127.0.0.1:8000/admin/>.

* The observation portal's **Web Interface** is accessible from <http://127.0.0.1:8080/>

* The **Configuration Database** is accessible from <http://127.0.0.1:7000/> and its admin interface is accessible from <http://127.0.0.1:7000/admin/>.

* The **Downtime Database** is accessible from <http://127.0.0.1:7500/> and its admin interface is accessible from <http://127.0.0.1:7500/admin/>.

* The **Science Archive** should be accessible from <http://127.0.0.1:9500/> and its admin interface is accessible from <http://127.0.0.1:9500/admin/>.

* The **minio bucket** which emulates S3 should be accessible from <http://127.0.0.1:9000/>

## Manually adding data to the Science Archive

The best way to add data to the science archive is by using the [ingester library](https://github.com/observatorycontrolsystem/ocs_ingester).
A single file has been automatically been uploaded in the startup routine of the science archive, and is visible at the archive api: <http://127.0.0.1:9500/frames>.

You can upload additional data as demonstrated in the following python script:

```python
import os
import requests
from ocs_ingester import ingester


# The following environment variables are required by the ingester.

# AWS keys can be found in the docker compose file, defined in the minio instances.
os.environ['AWS_ACCESS_KEY_ID'] = 'minio'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'minio123'
os.environ['AWS_DEFAULT_REGION'] = 'minioregion'
os.environ['BUCKET'] = 'ocs-example-bucket'

# This is the url pointing to the minio bucket. 
# For a bucket in AWS, the endpoint would follow the convention 
# of http://s3.<region-name>.amazonaws.com
os.environ['S3_ENDPOINT_URL'] = 'http://localhost:9000/'

# This is the science archive api endpoint
os.environ['API_ROOT'] = 'http://localhost:9500/'

# Test mode disables the opentsdb metrics reporting, which is not included 
# in the ocs_example stack.
os.environ['OPENTSDB_PYTHON_METRICS_TEST_MODE'] = 'True'


# Get the archive token for the ingester with the username and password 
# defined in the science archive service in the docker compose file. 
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


# Now that the environment is configured properly, we can begin the ingesting routine.

# Specify the file path. You can test it out on an example file here by running 
# this script from the root directory and using the following file path:
test_file_path = './example_data/ogg0m406-kb27-20210720-0305-s91.fits'
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
```
