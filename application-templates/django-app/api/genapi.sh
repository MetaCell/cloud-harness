#!/bin/bash

ROOT_PATH=$(realpath "$(dirname "$BASH_SOURCE")/../../..")
harness-generate servers --app-name "__APP_NAME__" "$ROOT_PATH"