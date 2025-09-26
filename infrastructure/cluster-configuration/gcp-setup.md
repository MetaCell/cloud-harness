## Google GKE setup

The easiest way to create the cluster is to use the GCP web console. Define a node pool that satisfies application requirements (no other particular requirements are generally necessary for the node pool/s).
The node pool can be always scaled to have a different node number, so the only important choice is the node type.
Also other node pools can be added at any point of time to the cluster to replace the original one.

After creating the cluster, use `gcloud` command line client to get the credentials in your machine:
- `gcloud init`
- `gcloud container clusters get-credentials --zone us-central1-a <CLUSTER_NAME>`


