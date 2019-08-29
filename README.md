# E-MISSION NEW ARCHITECTURE

The e-mission new architecture is a series of system changes designed to support individualized user storage, policy choices, and requests. To facilitate this, we have composed a series of modules, mostly running in containers, which represent the various components. These components are:

    * System Controller
    * User Data Storage
    * Data Simulation
    * Data Aggregation
    * Data Querying
    * Multimachine Communication

Each of these will sections covered in more detail, along with the code added/changed to implement it. Additionally we made changes to produce a variety of new images for containers, 

## Installation
To get everything to work properly with the current implementation, you need a linux machine with the following installations:

    * Anaconda Python3
    * Ecryptfs
    * Docker
    * Docker-Compose

### `Anaconda Python3`
On each machine we need a host process to provision docker instances which means you need access to `Python 3.5` or greater. Depending on the data analysis you wish to run you may need access to additional libraries, most of which should be supported by the `conda env` produced for the base e-mission server. You find the installation instructions on the main branch of the e-mission docs. Unfortunately the link to manual installation appears to be broken right now so I will link it when it returns.

It shouldn't be necessary to have as large an environment as the existing `conda env` provisions, but this sticks with some of the core design decisions we made in working on these changes "don't remove/optimize features until we get a working product." It for this reason that you see huge chunks of the e-mission code copied over (and consequentially creating a need to merge with the main repository) when we could probably succeed with a only including a much smaller subset.

### Ecryptfs

If you are planning on using or testing encrypted storage at rest you will need to run on a linux platform that can install `Ecryptfs`. This can be installed directly through `apt` on `Ubuntu`: 
```
$: sudo apt-get update
$: sudo apt-get install ecryptfs-utils
```
If you do not have a Linux distribution or your version of Linux does not support `Ecryptfs` then you will be unable to encrypt the storage and modifications will need to be made to prevent the existing implementation from crashing. 

We opted to use `Ecryptfs` mainly because it was easy to use and its encryption can be accomplished through mount commands. This does require that the containers are run with increased permissions however.

### Docker

Having `docker` is essential to running the modified architecture because every single component runs inside a container except for the component responsible for launching containers. You can find information on how to install `docker` on your platform from their [website](https://docs.docker.com/install/), as well as information on how `docker` works if you are unfamiliar.

### Docker-Compose

We additionally rely on `docker-compose` to actually launch our containers with specified input files. You can find the documentation on `docker-compose` also on their [website](https://docs.docker.com/compose/install/).

Here we have opted to rely on default `docker` rather than a more robust microservices implementation through either `docker swarm` or `kubernetes`. The former was a decision we made after we discovered that `docker swarm` couldn't support functionality we needed for our implementation whereas the latter we simply didn't have time to pursue.

## Architecture Code

To facilitate our new architecture we have added new code and docker functionality in a variety of locations. Regretably these are probably not the best locations to place this code and our changes can seem a bit disjoint in their placement. I will do my best to list what is located where and what its purpose is. Additionally with each section we will present a brief higher level overview of the intended purpose of each component, but this is not meant asa substitute for a detailed description of the architecture (which is in progress).

However before we can detail the exact component we need an overview of the components. Our new architecture basically consists of 3 components:

    1. Users
    2. Algorithm Providers
    3. A system controller

These components are then split further into various subcomponents but at a very high level users provide their data and have an abstraction of an individualized workstation through our "user cloud" abstraction. Algorithm providers interact directly which each user to acquire their necessary data and then aggregate their results as necessary. The system controller is responsible for providing the connection between users and their storage as well as algorithm providers access to users. By abstracting this component into a controller it allows us to dynamically reallocate resources.

### System Controller

The system controller is basically a central server that all participants connect to. It can perform a variety of tasks, some of which are:

    * Tell an algorithm instance where to find users.
    * Tell users where their user cloud is located.
    * Create a user cloud for a newly signed up user.
    * Pause and unpause the physical container for each cloud.

The last task is particularly important to us because our focus on placing everything in containers for increased isolation relies on an assumption that most of time each user cloud will not be processing data. This allows us to pause that instance which makes us better capable to provision our CPU resources more effectively (presumably at some cost to storing on disk).

Our actually implementation of this involves using `bottle.py` to create a server that receives post requests at some known address. Then our server holds mappings of users to their clouds locations as well as their current status ("Running" or "Paused"). Finally the server will periodically pause containers not in use according to some user specified timing requirements.

#### Files
The actually files changed or added to implement the controller (relative to the e-mission-server base directory) are:

    * `launch_machine.py` - Helper script to launch the controller.
    * `conf/net/machines.json.sample` - Example configuration used to specify the controller
    * `emission/net/api/controller.py` - Actual code used to provide the server.

We also interact with existing e-mission files as well as some possible helper scripts but we will not detail them here.

### User Data Storage

User data storage is done through our "user cloud" concept. The user cloud is currently simply a copy of the e-mission server but with extra information (for example the ability to send the user's key to mongo to deploy the database over an encrypted file system). For this reason we have opted to included all the original e-mission code with some extra functionality. This conseqeuentially means that code sizes are a lot bigger than should be necessary (because we include a lot of files we didn't modify) and we haven't removed any of the code that is no longer relevant (for example each user still needs to log in and register despite being the only user in the container. There should be a more modular approach that would for example allow us to only swap in the `cfc_webapp.py` file into an existing docker image that otherwise contains the rest of the e-mission code but we have not looked into doing this. 

The presence of additional user clouds per machine also required us to provision ports dynamically and present that information through environment variables (to make each instance unique from the same start script). This is NOT a robust process and understanding the exact rules for naming likely requires further investigation.

#### Files
The actually files changed or added to implement the user cloud (relative to the e-mission-server base directory) are:

    * `emission/net/api/cfc_webapp.py` - Actual code for the e-mission web server. You can find my changes in a section commented "Nick's changes"

We also interact with existing e-mission files as well as some possible helper scripts but we will not detail them here.

### Data Simulation

### Data Aggregation

#### Files
The actually files used to implement the controller (relative to the e-mission-server base directory) are:

    * `launch_machine.py` - Helper script to launch the controller.
    * `conf/net/machines.json.sample` - Example configuration used to specify the controller
    * `emission/net/api/controller.py` - Actual code used to provide the server.

We also interact with existing e-mission files as well as some possible helper scripts but we will not detail them here.

### Data Querying
#### Files
The actually files used to implement the controller (relative to the e-mission-server base directory) are:

    * `launch_machine.py` - Helper script to launch the controller.
    * `conf/net/machines.json.sample` - Example configuration used to specify the controller
    * `emission/net/api/controller.py` - Actual code used to provide the server.

We also interact with existing e-mission files as well as some possible helper scripts but we will not detail them here.

### Multimachine Communication

#### Files
The actually files used to implement the controller (relative to the e-mission-server base directory) are:

    * `launch_machine.py` - Helper script to launch the controller.
    * `conf/net/machines.json.sample` - Example configuration used to specify the controller
    * `emission/net/api/controller.py` - Actual code used to provide the server.

We also interact with existing e-mission files as well as some possible helper scripts but we will not detail them here.

### Docker Changes

You can find information about how to run the code in `docker/README.md`. One important piece of information is that testing any changes requires pushing to github (and likely requires that you modify the docker file and relevant start scripts to reflect that endpoint). The reason is that the existing code base creates the docker image by executing `git clone` when building the image. We made further modifications by having the start script pull the latest commit to avoid rebuilding the image, but all of this indicates that testing changes require pushing to a remote repository.

You can find the details on how constructing the docker instances work in the `docker/README.md` as well.

### Reading the Code

To get familiar with our implementation and changes we suggest the following reading order:

1. Multimachine Communication - This should consist mostly of raw docker commands so hopefully it gives a clear picture of what is actual happening.
2. `bottle.py` - Reading and understanding how a bottle server works is the next step for understanding what the controller and user cloud are based around.
3. `controller.py` and `cfc_webapp.py` - Together these should give an overview of how the controller and user cloud actually exist. It should also highlight what is happening inside containers.
4. Data generation scripts - Both how to call them and what is happening should provide an understanding of how to actually fill a user cloud.
5. Data Aggregator and Data Querier - These together should provide an example of how an application may query and interact with our user cloud
6. Scripts to run the whole process (`runNewArch.py` for example) - These should give you an example how use can construct experiments to test the architecture.

## Setup and Teardown

You can find information on how to actually run the code and build the necessary images inside the `README` in the docker directory.
