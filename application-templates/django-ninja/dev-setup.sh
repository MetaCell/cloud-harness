#!/usr/bin/env bash

CURRENT_PATH=$(pwd)
CH_DIRECTORY="../../cloud-harness"
INSTALL_PYTEST=false
CURRENT_DIRECTORY="$(pwd)"
APP_NAME="__APP_NAME__"

pip_upgrade_error() {
    echo "Unable to upgrade pip"
    exit 1
}

install_error () {
    echo "Unable to install $1" 1>&2
    exit 1
}

while getopts ch_directory:pytest arg;
do
    case "$arg" in
        ch_directory) CH_DIRECTORY=${OPTARG};;
        pytest) INSTALL_PYTEST=true;;
    esac
done

pip install --upgrade pip || pip_upgrade_error

# Install pip dependencies from cloudharness-base-debian image

if $INSTALL_PYTEST; then
    pip install pytest || install_error pytest
fi

pip install -r "$CH_DIRECTORY/libraries/models/requirements.txt" || install_error "models requirements"
pip install -r "$CH_DIRECTORY/libraries/cloudharness-common/requirements.txt" || install_error "cloudharness-common requirements"
pip install -r "$CH_DIRECTORY/libraries/client/cloudharness_cli/requirements.txt" || install_error "cloudharness_cli requirements"

pip install -e "$CH_DIRECTORY/libraries/models" || install_error models
pip install -e "$CH_DIRECTORY/libraries/cloudharness-common" || install_error cloudharness-common
pip install -e "$CH_DIRECTORY/libraries/client/cloudharness_cli" || install_error cloudharness_cli

# Install pip dependencies from cloudharness-django image

pip install -e "$CH_DIRECTORY/infrastructure/common-images/cloudharness-django/libraries/cloudharness-django" || install_error cloudharness-django

# Install application

pip install -r "$CURRENT_DIRECTORY/backend/requirements.txt" || install_error "$APP_NAME dependencies"
pip install -e "$CURRENT_DIRECTORY/backend" || install_error "$APP_NAME"