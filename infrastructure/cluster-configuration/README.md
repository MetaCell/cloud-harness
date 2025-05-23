# Cluster configuration

## Simple setup on an existing cluster

### TLDR;
1. Create Kubernetes cluster (e.g minikube or google cloud)
1. Initialize kubectl credentials to work with your cluster 
1. Run `source cluster-init.sh`  (This script installs the ingress-nginx controller and cert-manager using Helm in the configured k8s cluster.)

### Cert-manager

Follow [this](https://cert-manager.io/docs/installation/kubernetes/) instructions to deploy cert-manager 

### Ingress

Ingress controller is the entry point of all cloudharness applications.
Info on how to deploy nginx-ingress can be found [here](https://kubernetes.github.io/ingress-nginx/deploy/).

```
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx
```

On localclusters and GCP/GKE, the nginx-ingress chart will deploy a Load Balancer with a given IP address, while in other environments, you may need to configure the Load Balancer manually. Use that address to create the CNames and A records for the website.



## GCP GKE cluster setup

GKE setup is pretty straighforward. Can create a cluster and a node pool from the google console and internet facing load balancers are directly created with the ingress controller.

For additional info see [here](gcp-setup.md).

## AWS EKS setup
AWS requires come additional steps to install the load balancer and the ingress, see [here](./aws-setup.md)
