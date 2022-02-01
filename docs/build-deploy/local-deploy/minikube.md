General steps:
1. Install Minikube
1. Initialize Minikube cluster
1. Set up `kubectl` command line tool
1. Set up the Docker registry
1. Run the build script


Step 5,6,7 differ in case we run Minikube in the same or different machine from the client in which we make the development and build.

## Install Minikube
A Minikube installation must be accessible and activated on the command line tool `kubectl`.
See also https://kubernetes.io/docs/tasks/tools/install-minikube/


## Initialize Minikube cluster

At least 6GB of ram and 4 processors are needed to run MNP

To create a new cluster, run
```
minikube start --memory="6000mb" --cpus=4
```


To verify the installation, run
```
kubectl cluster-info
```

Enable ingress addon:

```
minikube addons enable ingress
```

## Setup CloudHarness

Follow the general steps suggested [here](./README.md)

## Procedure if Minikube and the client are in the same machine

### Set up Kubectl
The easiest way is to install Minikube in the same machine in which you do the build.

Kubectl will be available right after the installation.

### Set up Docker

Running
```asciidoc
eval $(minikube docker-env)
```
will build images directly on the Minikube environment.

### Run the build script

Run the following
```bash
cd deployment
harness-deployment cloud-harness . -b -l
```

## Procedure with Minikube and client/build on different machines

### Setup kubectl
If Minikube is installed in a different machine, the following procedure will allow to connect kubectl.

1. Install kubectl in the client machine
1. copy `~/.minikube` from the client to the server (skip cache and machines)
1. Copy `~/.kube/config` from the Minikube server to the client machine (make a backup of the previous version) and adjust paths to match the home folder on the client machine

#### Kube configuration copy
If you don't want to replace the whole content of the configuration you can copy only
 the relevant entries in `~/.kube/config` from the server to the client on `clusters`, `context`

Examples:

On `clusters`
```yaml
- cluster:
    certificate-authority: /home/user/.minikube/ca.crt
    server: https://192.168.99.106:8443
  name: minikube
```

On `context`
```yaml
- context:
    cluster: minikube
    user: minikube
  name: minikube
```

On `users`
```yaml
- name: minikube
  user:
    client-certificate: /home/user/.minikube/client.crt
    client-key: /home/user/.minikube/client.key
```

Set default context:
```yaml
current-context: minikube
```

### Set up the Docker registry

In the case we are not building from the same machine as the cluster (which will always happen without Minikube),
we need a way to share the registry.

Procedure to share localhost:5000 from a kube cluster

In the minikube installation:

```bash
minikube addons enable registry
```

In the machine running the infrastructure-generate script, run

```bash
kubectl port-forward --namespace kube-system $(kubectl get po -n kube-system | grep registry | grep -v proxy | \awk '{print $1;}') 5000:5000
```

### Run the build script

After the registry is forwarded to localhost:5000, we can deploy by specifying the registry the image names will be adjusted and all images will be pushed to the minikube registry.

```
cd deployment
harness-deployment cloud-harness . -b -l -r localhost:5000
```

## Use the dashboard to monitor your deployment

To visually monitor the installation, run
```
minikube dashboard
```