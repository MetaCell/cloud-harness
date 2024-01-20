# Custom JupyterHub

This Helm chart is forked from the main JupyterHub helm chart and adapted to CloudHarness path structure.

The main personalizations happen in the file `jupyterhub_config.py` in order to implement the following 
dynamic behaviours like:
 - Use a different image based on current path/parameter
 - Mount custom volumes

## Node selector for Jupyter hub apps

A Jupyter Hub application can configure the kubernetes node selector in order to make sure that the app 
will run on nodes matching the app's node selector config.

To set up a node selector add the follwoing lines to the app's values.yaml file:
 ```
harness:
  jupyterhub:
    spawnerExtraConfig:
       node_selectors:           # optional node pool for these pods
        - key: ch/nodepool       # the name of the meta data key of the node (can be set at node pool level)    
          operator: In           # In, NotIn, Exists, DoesNotExist. Gt, and Lt.
          values: pool-highcpu   # k8s highcpu instance pool
          matchPurpose: require  # require | prefer | ignore
```

## Customizations

CloudHarness pre puller of tasks images support
To support the pre pulling of task images see (https://github.com/MetaCell/cloud-harness/issues/657)
the template `templates/image-puller/_helpers-daemonset.tpl` has been changed (see line 167 and on)

TODO: remember to implement/revise this code after you have updated/changed the templates of JupyterHub

## How to update

The helm chart is based on the [zero-to-jupyterhub](https://github.com/jupyterhub/zero-to-jupyterhub-k8s/) helm chart.

1. Run update.sh [TAG] # Do not use latest!
2. Restore from the diff files with EDIT: CLOUDHARNESS

Customize notebook image: quay.io/jupyterhub/k8s-singleuser-sample:[TAG]

