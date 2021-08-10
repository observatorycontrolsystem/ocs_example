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

By default, the Observation Portal will have a single account created with the username `test_user` and the password `test_pass`. This can be used to login to the Observation Portal, or the admin interface of the Science Archive, Configuration Database, or Downtime Database.

Minio is setup with the access key `minio_access_key` and secret `minio_secret`. 

These can be configured in the docker compose file.

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

* The **Observation Portal** API is accessible from <http://localhost:8000/api/>, and its admin interface is accessible from <http://localhost:8000/admin/>.

* The observation portal's **Web Interface** is accessible from <http://localhost:8080/>

* The **Configuration Database** is accessible from <http://localhost:7000/> and its admin interface is accessible from <http://localhost:7000/admin/>.

* The **Downtime Database** is accessible from <http://localhost:7500/> and its admin interface is accessible from <http://localhost:7500/admin/>.

* The **Science Archive** is accessible from <http://localhost:9500/> and its admin interface is accessible from <http://localhost:9500/admin/>.

* The **minio server** which emulates S3 is accessible from <http://localhost:9000/>. 


## Adding data to the Science Archive

The easiest way to add data to the science archive is by using the [ingester library](https://github.com/observatorycontrolsystem/ocs_ingester).
You can find a working example at [scripts/science_archive/ingest_sample_data.py](scripts/science_archive/ingest_sample_data.py).
This script is run once when starting up the ocs_example project and uploads an example file for each completed observation. All data in the science archive can be found in the [science archive api](http://localhost:9500/frames/).
More information about configuring and running the ingester can be found in the [ingester docs](https://ingester.readthedocs.io/en/latest/README.html).
