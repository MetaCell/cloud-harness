#!/bin/bash

fastapi-codegen --input openapi.yaml --output app -t templates && mv app/main.py ../backend/ && mv app/models.py ../backend/openapi/
rm -rf app

echo Generated new models and main.py
