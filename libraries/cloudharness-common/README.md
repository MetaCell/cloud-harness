# CloudHarness backend library
CloudHarness - Python core library.

The Cloudharness core library provides horizontal utilities needed inside custom 
applications and tasks.

## How to use

In order to use all `cloudharness` functionalities inside the cluster you must
define your Dockerfile depending on the base cloudharness as following:

```Dockerfile
ARG REGISTRY
ARG TAG=latest
ARG CLOUDHARNESS_BASE
FROM $CLOUDHARNESS_BASE
```

## Requirements

Python 3.4+

## Installation

Install with setuptools from sources

```
cd libraries/cloudharness
pip install .
```