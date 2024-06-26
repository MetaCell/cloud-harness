# OpenAPI generated server

## Overview
This server was generated by the [OpenAPI Generator](https://openapi-generator.tech) project. By using the
[OpenAPI-Spec](https://openapis.org) from a remote server, you can easily generate a server stub.  This
is an example of building a OpenAPI-enabled Django FastAPI server.

This example uses the [Django](https://www.djangoproject.com/) library on top of [FastAPI](https://fastapi.tiangolo.com/).

## Requirements
Python >= 3

## Local backend development
```
# store the accounts api admin password on the local disk

mkdir -p /opt/cloudharness/resources/auth/
kubectl -n mnp get secrets accounts -o yaml|grep api_user_password|cut -d " " -f 4|base64 -d > /opt/cloudharness/resources/auth/api_user_password

# Make the cloudharness application configuration available on your local machine
cp deployment/helm/values.yaml /opt/cloudharness/resources/allvalues.yaml
```
