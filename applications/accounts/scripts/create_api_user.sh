#!/bin/bash

NAMESPACE=${CH_ACCOUNTS_REALM}
USERNAME=$(cat /opt/cloudharness/resources/auth/api_user_username)
PASSWORD=$(cat /opt/cloudharness/resources/auth/api_user_password)

set -e
echo Creating API user

# create the user and reload keycloak
/opt/jboss/keycloak/bin/add-user-keycloak.sh -u ${USERNAME} -p ${PASSWORD}
