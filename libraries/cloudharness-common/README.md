# CloudHarness backend library
CloudHarness - Python core library.

The Cloudharness core library provides horizontal utilities needed inside custom 
applications and tasks.

## How to use

In order to use all `cloudharness` functionalities inside the cluster you must
define your Dockerfile depending on the base cloudharness as following:

```Dockerfile
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


# Middleware

This library also contains a Flask and Django Middleware module which is needed 
for using the Cloudharness AuthClient package.
These middlewares use the request header `Authorization` to set the `ch_authentication_token`
contextvar in `cloudharness.middleware.__init__.py`. The AuthClient uses the authentication token
to validate the request and retrieve the Keycloak user

## Flask Middleware

The Flask middleware is activated in the `init_flask` and will be executed on each request. There
is no need to manually activate this middleware.


## Django Middleware

This library also contains a Django Middleware module which is needed to use the Cloudharness AuthClient.
To activate this middleware add `cloudharness.middleware.django.CloudharnessMiddleware` to your
Django middleware classes.

E.g. in Django settings.py
```
...

MIDDLEWARE = [
    ...
    'cloudharness.middleware.django.CloudharnessMiddleware',
    ...
]

...
```
