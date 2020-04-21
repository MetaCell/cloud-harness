# Infrastructure

Here we put all the resources intended to install and deploy the platform on Kubernetes.

## Relevant files and directory structure
 - `base-images`: base Docker images. Those images can used as base images in CloudHarness apps and tasks.
 - `common-images`: Static images. Those images can derive from base images can be also used as base images in CloudHarness apps and tasks. 
 
## Base images and common images

The main difference between the base images and common images is that base images are built in the root context, while
common images are built in a local context.
So, base images are general purpose and are mainly used to provide access to custom libraries, while common images can have
a specific purpose (e.g. enable widely used libraries for tasks).




