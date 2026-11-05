#!/usr/bin/env bash

CURRENT_PATH=$(pwd)
INSTALL_PYTEST=false
CURRENT_DIRECTORY="$(pwd)"
APP_NAME="__APP_NAME__"
LIBRARIES_DIRECTORY="$CURRENT_DIRECTORY/libraries"

pip_upgrade_error() {
    echo "Unable to upgrade pip"
    exit 1
}

install_error () {
    echo "Unable to install $1" 1>&2
    exit 1
}

while getopts p arg;
do
    case "$arg" in
        p) INSTALL_PYTEST=true;;
    esac
done

pip install --upgrade pip || pip_upgrade_error

# Install the vendored CloudHarness libraries

if $INSTALL_PYTEST; then
    pip install pytest || install_error pytest
fi

pip install -r "$LIBRARIES_DIRECTORY/models/requirements.txt" || install_error "models requirements"
pip install -r "$LIBRARIES_DIRECTORY/cloudharness-common/requirements.txt" || install_error "cloudharness-common requirements"
pip install -r "$LIBRARIES_DIRECTORY/cloudharness-django/requirements.txt" || install_error "cloudharness-django requirements"

pip install -e "$LIBRARIES_DIRECTORY/models" || install_error models
pip install -e "$LIBRARIES_DIRECTORY/cloudharness-common" || install_error cloudharness-common
pip install -e "$LIBRARIES_DIRECTORY/cloudharness-django" || install_error cloudharness-django

# Install application

pip install -r "$CURRENT_DIRECTORY/backend/requirements.txt" || install_error "$APP_NAME dependencies"
pip install -e "$CURRENT_DIRECTORY/backend" || install_error "$APP_NAME"