# Define and use base and common images

## Relevant files and directory structure
 - `base-images`: base Docker images. Those images can used as base images in CloudHarness apps and tasks.
 - `common-images`: Static images. Those images can derive from base images can be also used as base images in CloudHarness apps and tasks. 
 
## Base images and common images

The main difference between the base images and common images is that base images are built in the root context, while
common images are built in their local context.
So, base images are general purpose and are mainly used to provide access to shared libraries alongside the solution, while common images can have
a specific purpose (e.g. enable widely used application stacks to inherit from).

## Use in applications and tasks

After generating the codeChange the Dockerfile in order to inherit from the main Docker image need to:

1. Add the image as a build dependency to the values.yaml file of your application. The name of the image corresponds to the directory name where the Dockerfile is located 

```
harness:
  dependencies:
    build:
    - cloudharness-base
```

2. Refer to the base image with the uppercased-underscored name of the dependency as an argument
```dockerfile
ARG CLOUDHARNESS_BASE
FROM $CLOUDHARNESS_BASE
```

> Notice: the dependency may work if other applications in the same deployment declare the same dependency. Anyway, it'a always recommended to specify the dependency wherever it is used

In multi-stage builds, more than one build dependency can be added and referred.

In workflow tasks, the build dependency must be specified in the main application where it is defined.

## Default images

CloudHarness defines the following base images:
- `cloudharness-base`: python-alpine with cloudharness common libraries preinstalled
- `cloudharness-base-debian`: python-debian with cloudharness common libraries preinstalled
- `cloudharness-frontend-build`: node image to be used as a build step in npm based frontends

Also the following common images are defined:
- `cloudharness-flask`: common ground image to create Flask backends

## Override base and common images from CloudHarness

To override a base or common image just create the same directory path in your 
solution. The overriding can be used to replace files used in the build process or the Dockerfile itself.

For example, overriding `cloudharness-base` could be useful to change some behaviour in the CloudHarness
libraries or to provide new libraries to share within all applications.

To override cloudharness-base, create a directory `MY_SOLUTION/infrastructure/base-images/cloudharness-base`
then run `harness-deployment cloudharness MY_SOLUTION`

