# E-MISSION User Private Clouds

This repository contains the implementation of User Private Clouds (UPC) and the relevant services used to operate select e-mission functionality within UPC. A higher level description of UPC is available in my [technical report](https://www2.eecs.berkeley.edu/Pubs/TechRpts/2020/EECS-2020-130.html).

## Installation
To get everything to work properly with the current implementation, you need at least one linux machine with the following installations:

* Anaconda Python3
* Ecryptfs
* Docker
* Either docker-compose or kubernetes

### Anaconda Python3
On each machine we need a host process to provision docker instances which means you need access to `Python 3.5` or greater. Depending on the data analysis you wish to run you may need access to additional libraries, most of which should be supported by the `conda env` produced for the base e-mission server. You find the installation instructions [here](https://github.com/e-mission/e-mission-docs/blob/master/docs/install/manual_install.md).

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

### Docker-Compose or Kubernetes

Our current implementation supports either using docker-compose with a set of servers we built or kubernetes to launch the UPC services. There are tradeoffs with each selection, which hopefully these will do a good job of summarizing. We cannot use docker-swarm because ecryptfs requires sudo permissions, which are not available with docker-swarm.

Docker-Compose Advantages:
  * Simple to use.
  * Pausing containers is possible. This is useful if you need many concurrent users.
  * Each container is very lightweight.
    
Docker-Compose Disadvantages:
  * Not representative of a real system.
  * No native distributed storage.
  * Currently no support for recovery upon whole machine failure.
  * Server upkeep cannot no longer be a cloud task.
  * Less isolation than Kubernetes offers.

Kubernetes Advantages:
  * Designed to balance pods across machines.
  * Easy configuration on cloud machines.
  * Recovery upon machine failure
  * Better able to set resource limits.
  * Overall more development.

Kubernetes Disadvantages:
  * Pods are a bad fundamental layer and the number of pods that can be spawned at once is very small. You may need to get creative with how you reuse pods.
  * No support for pausing containers.
  * Constructing a Kubernetes cluster may be more difficult than just installing docker.
  * Kubernetes has a harsher learning curve because it has more functionality.

Ultimately I would suggest using Kubernetes. However, if you need many concurrent users for deployment you will need to decide how to allocate users (it will be far too slow to delete pods as needed) and you may need to pick the best way to recycle containers. If this proves too difficult and pausing containers is essential to usable performance, then you may need to settle for the docker-compose based implementation.

#### Installing Docker-Compose

You can find the documentation on `docker-compose` and how to install it on this [website](https://docs.docker.com/compose/install/). 

#### Installing Kubernetes

To run kubernetes there are a few necessary components. First you must install [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/) and its dependencies on at least one machine, whichever machine hosts the service router. Next you will need access to a Kubernetes cluster. For testing purposes you will probably first want to install [minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/). Minikube containers can interact with each other so you can test correctness with a single machine. You may also need to configure your docker images to work properly with minikube, either by uploading the images to a remote registry from which minikube will download or by [building the images directly in minikube](https://stackoverflow.com/questions/52310599/what-does-minikube-docker-env-mean). 

While it may be possible to run multi-machine cluster using minikube, I am not familiar with how to do so. Instead I recommend using a cloud provider that has kubernetes support. In my technical report I found the [Google Kubernetes Engine](https://cloud.google.com/kubernetes-engine) particularly easy to use and if you are a student you may have free credits. However when transitioning to a cloud kubernetes engine you may have to make additional changes to adhere to requirements of the cloud provider. For example, in my experience I needed to change all of the docker images paths to correspond to Google's [container registry](https://cloud.google.com/container-registry), and I needed to modify the firewall rules to allow external traffic to access the ports the containers would occupy (because we use the NodePort service type).

## Code Overview

This section will give a brief overview of how to code is organized and where you will need to make changes to alter various functionality. It is not intended to serve as a comprehensive overview to UPC and the aforementioned report will likely be more beneficial.

### `conf/`

This folder containers the information necessary for configuring the service router and the user services. The main file that you might need to edit `conf/machines.json.sample`. If you opt to replace this with a different file then you will need to edit `conf/machine_configs.py` (which you will also need to edit if you add any additional configuration details.

Machines.json.sample contains a list of shorthands for api names as well as set of configuration details. At a minimum before you begin you will need to set:
  * **service\_router\_ip** with the IP address of the machine hosting the service router
  * **Machines** with the ips of the machines in your cluster. If you are using docker-compose you need to list every machine and place a weight for how likely it is to choose each machine. If you are using kubernetes you only need to list a single machine (and a dummy weight) as services are accessible from all machines in a Kubernetes cluster with our configuration.
  * **upc\_mode** with either "kubernetes", if you are using a kubernetes deployment, or "docker" if you are using a docker-compose deployment

There are other fields you may wish to modify, notably the ports upon which each server runs, but it is not necessary to change these to get a working implementation.

The most important aspect of your configuration is that it must be consistent across all your machines and services to ensure it works properly.

### `service_router/`
This directory contains all the files used to orchestrate spawning various services across your cluster of machines. It contains the following files you may need to use or change:

  *  `router.py`: Launches the service router.
  *  `swarm.py`: A server that you will need to launch on each machine if you are running with docker-compose
  *  `kubernetes_services.json`: A json file which for each known service contains the location of each pod file, service file, and the name of the container that acts a server within the pod. If you are using kubernetes and add a service you will need to add an entry to this file.
  *  `docker_services.json`: A json file which for each known service contains the location of the docker-compose file. If you add a service and use docker-compose you will need to add an entry to this file.

Additionally, if you intended to alter or add functionality to the service router you may need to modify one of the python files.

### `shared_apis/`

This directory contains a set of apis that will likely be shared by clients, aggregators, or services. The biggest reason you may need to modify one of these scripts is if you need to use one of the e-mission database views that are not currently supported then you may want to `index_classes.py`. When using differential privacy, some example queries are provided in `queries.py`. The other files support the APIs for interacting with the pm and the service router.

### `services/`

The services directory contains a set of sample services that the service router can spawn. Admittedly, each service should probably be included as a submodule if it is included at all. The most important components for each service are the presence of a docker image (which is why for development all of the code is provided) and the configuration files for kubernetes and docker-compose. In our example we have provided 4 service: 
  * The Permission Manager (PM): The service that is provided a user's storage key.
  * Pipeline: A service that runs the e-mission intake pipeline.
  * Metrics: A service that replaces the metrics endpoint in the `cfc_webapp.py` of the e-mission server.
  * Count: A service that performs example count queries based on location and date.

Both Pipeline and Metrics are derived from the base e-mission server and are unoptimized. If there is a significant reason to do so, I can work on removing the unnecessary files, but this could be a timeconsuming or tedious process. There is also the question of how to update e-mission server components upon which the service relies, which is why I maintain the same code structure, with only two modified files: `emission/net/api/cfc_webapp.py` and `emission/core/get_database.py`.

### `client_scripts/`

This directory contains a series of scripts that simulate the actions performed by a client device. Currently there are only a few examples such as upload and downloading data or launching and running user specified services.

### `aggregator_scripts/`

This directory contains a series of scripts meant to represent the roles of aggregators when engaging with UPC. In a real implementation, the aggregator should always contact each user through their device applications and have the device interact with the service router directly. As a result all of our aggregators function by interacting with scripts in the `client_scripts` folder. Perhaps a more realistic implementation would require each client to have a server application which functions as a device application, but instead our application will just launch the client scripts directly. Additionally, to all for an easy to understand demo our example aggregators undergo the process of having users upload data and run the pipeline, which is not realistic. Instead a more reasonable approach would be to rely on whatever data is already processed.

## Example Usage

In this section we will demo scripts that are used to run client scripts or aggregation scripts. These should serve as examples of how to create a new client or aggregator. Additionally, to provide some insights into how the existing code is built the process will include not just the steps for you to run but what is happening with each step.

Finally, its worth noting that both setups assume no existing users or persistent storage. If you rely on either your steps will likely be much simpler but may require altering the service router to properly associate each user with their longterm storage.

### Shared Setups

Whether you are running an example of a client or aggregator there are a few steps that you will need to be successfully operated.

  1. Make sure each machine in your cluster has the necessary installations.

  2. Modify the configurations in `/conf/machines_sample.json` matches the machines in your cluster. To avoid any issues you should keep this synchronized across all the machines in your cluster.

  3. Make sure you have each docker image. You can rebuild each docker script by running `build_images.sh` in bash. If you find yourself frequently editing a service you will likely find it useful to modify the dockerfile to import your self from a github repository. If you choose to do this you can modify the first step of the `setup_script.sh` found in the respective service directories to pull changes to the repo as an initial runtime step and avoid the time necessary to rebuild the image (which can take some time).

  4. Select a machine on which to run the service router and load the e-mission anaconda environment. If this is your first time then run 
  ```
  $ source setup/setup.sh
  ```
  In your terminal. If you have already completed this step then run
  ```
  $ conda activate emission
  ```
  in each terminal.

  If you are running with docker-compose then you will need to repeat this step on each additional cluster.

  5. Configure you cluster to properly interact with the service router. If you are using kubernetes this requires ensuring your `kubectl` is properly configured. If you are using docker-compose you will need to launch a server on each machine, including the machine with the service router if it is part of the cluster, by running:
  ```
  $ ./e-mission-py.bash service_router/swarm.py
  ```

  6. Launch the service router on one of your machines. To do so run:
  ```
  $ ./e-mission-py.bash service_router/router.py
  ```

Now you have the service router running and it knows about your cluster. At this point you can run either the client or aggregator example.

### Client Script Steps

### Aggregator Script Steps

## Missing Features and Possible Future Improvements
This section is a list of shortcomings with the current implementation that could benefit from either further discussion or further development.

### TLS Support
The code presented here should hold the necessary changes to add support for TLS, but that functionality is largely untested. I did demonstrate that TLS with self-signed certificates works with an implementation very similar to the code give in this file, but this feature has not been tested since support for Kubernetes was added (and may no longer work on the docker-compose version either). At a minimum you will need to `certificate_bundle_path` variable within `/conf/machines.json.sample` to refer to the path to validate the certificates you are using and indicate that seek to use tls in `/conf/machines.json.sample`. I have never implemented TLS with Kubernetes but if you wish to do so these [steps](https://kubernetes.io/docs/tasks/tls/managing-tls-in-a-cluster/) may prove helpful.

### Service Validation
One feature missing from the current implementation is a process that validates that each service spawned is what is expected. [Docker image ids are digests of their hash values](https://windsock.io/explaining-docker-image-ids/), so validating that the image downloaded is what it claims to be should be simple. Additionally, to add support for matching user expectations, we could extend the service launch step to return the image id, so the user could verify that the image is what they expected. For validating containers, the problem is more difficult because the container is dynamic and potentially changing. However, we can impose additional constraints, such as checking for volumes, using existing tools, examples of which are found [here](https://github.com/e-mission/e-mission-upc-aggregator/issues/6).

### Authentication
One glaring weakness with the current implementation of the service router is that it has no means of authenticating users. As a result, any user can for example request that all services be deleted. This is the current situation because I have no real users and as a result no need to impose access permissions across fake accounts. However, in the future it will probably be helpful to launch the service router alongside a database and store information about which users can invoke requests on which services. Similarly, we should probably add some support for ensuring that a PM that is spawned with a key along takes requests from authorized services or users, although it is unclear what the best of way of doing so would be.

### Optimized Services
The services provided are not optimized for the UPC architecture. For example, despite only being able to run the intake pipeline, the pipeline service contains almost of all of the existing e-mission code and still expects each user to store a uuid in its database (despite being the only user). If is would beneficial to significantly reduce to the code size or optimize the implementation I can consider doing so in the future, but this will also make it harder to try and update a server component upon which a service relies.

### Kubernetes Limitations
As noted above Kubernetes has limitations with regards to the number of pods that can spawn at once and has a significant cost to remove a pod. As a result, future work needs to be focused on reusing existing pods. It may also prove useful to more aggressively explore the limits that are promised in a cluster. It may be possible that by promising each pod a very very small percentage of CPU and allowing it to allocate more when needed and then relying on most containers to be inactive most of the time that it is possible to allocate many more pods to the point where the number of allocate pods is tolerable or even comparable to just allocating containers.

### Automated Pausing or Deletion
Currently the service router takes no special efforts to ensure fairness with respect to pausing or tearing down containers. Instead we rely entirely on having clients communicate with the service router that they are finished operating. In any real deployment this is likely unacceptable so we probably want to institute a process to either pause or delete services that are operating for too long. If this has interest I can try and revive a previous partial implementation I had when this run solely with docker-compose.

### Reusable Storage
Configuring either kubernetes or docker-compose with persistent volumes should hopefully be a straightforward task. However, if you opt to delete a service the existing implementation will not properly locate the previous volume location. At the time of writing this is because we haven't equipped distributed storage, so in the future this will need to be supported. This likely requires adding a component to the service router that maps users to volume locations, again likely requiring a persistent database. Additional steps may be required if volumes are by default specified in the configuration files.
