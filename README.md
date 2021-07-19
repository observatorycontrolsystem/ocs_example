# OCS Example Project

## A pre-populated demo of the OCS services

This example project provides a docker-compose file which launches an [Observation Portal](https://github.com/observatorycontrolsystem/observation-portal), a [web interface](https://github.com/observatorycontrolsystem/ocs-example-frontend) for the observation portal, a [Configuration Database](https://github.com/observatorycontrolsystem/configdb), a [Downtime Database](https://github.com/observatorycontrolsystem/downtime), and an [Adaptive Scheduler](https://github.com/observatorycontrolsystem/adaptive_scheduler), all connected together with pre-populated sample data.

## Credentials

By default, the Observation Portal will have a single account created with the username `test_user` and the password `test_pass`. This can be used to login to the Observation Portal or the admin interface of the Configuration or Downtime Databases.

## Example Data

A number of management scripts are run on container startup to pre-populate the database with some example data

### Configuration Database

* `init_e2e_data` - This command creates a site, enclosure, telescope, camera, and instrument with a few filters and a readout mode. This should be the minimum information necessary to submit a request.

### Downtime Database

* `create_downtime` - This command creates a downtime on a given site, enclosure, and telescope at a given time, for a given reason. This is a called by the docker-compose file to set up a downtime in the past and in the future.

### Observation Portal

* `create_application` - This command creates an oauth application link in the project which gives that application the ability to authenticate off of the oauth backend.
* `create_user` - This command creates a superuser account and associated Profile, and creates an associated API Token.
* `create_semester` - This command creates a Semester with the given id, start, and end times, which default around the present time.
* `create_proposal` - This command creates a proposal with the specified properties, assigns the given user as the proposal PI, and optionally creates time allocations with 100 hours of all types of observing time on all schedulable instruments for the current Semester. There must be an existing, current semester defined to be able to create time allocations for the proposal.
* `example_requests` - This command creates a set of RequestGroups with different observation types and states, and a set of associated Observations for the Requests that should have been attempted. It requires that a valid User and Proposal be passed in. Requests are created both in the past and in the future of the current time. Targets are choosen randomly out of a predefined list if they are visible given the defined sites in Configdb.

## Running the example

First, you must ensure that you pulled down the submodule `docker-postgresql-multiple-databases`. This can be done when cloning the repo by adding `--recurse-submodules --remote-submodules` to your `git clone` command. It could also be done after cloning the base repo by running `git submodule init` followed by `git submodule update` in the base repo directory. After doing either of these, your `docker-postgresql-multiple-databases` directory should contain a file named `create-multiple-postgresql-databases.sh`, which is used to create multiple databases in the same postgresql container.

This example requires access to the docker images of observatory control system components (all on dockerhub). It also requires your system to be running docker and have docker-compose installed. To run the example applications, run
`docker-compose up -d` from within this directory. Once running, you should be able to use the credentials given above to access the admin interface of any of the applications, or to login and view/submit requests on the Observation Portal's web interface.

By default, the docker-compose file has ports set up such that:

* The **Observation Portal** should be accessible from <http://127.0.0.1:8000/api>

* The observation portal's **Web Interface** should be accessible from <http://127.0.0.1:8080>

* The **Configuration Database** should be accessible from <http://127.0.0.1:7000>

* The **Downtime Database** should be accessible from <http://127.0.0.1:7500>

* The **Science Archive** should be accessible from <http://127.0.0.1:9500>
