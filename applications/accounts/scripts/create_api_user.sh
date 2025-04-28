#!/bin/bash

NAMESPACE=${CH_ACCOUNTS_REALM}
USERNAME=admin_api
PASSWORD=$(cat /opt/cloudharness/resources/auth/api_user_password)

set -e
echo Creating API user

# create the user and reload keycloak
/opt/keycloak/bin/kcadm.sh create users -s "username=$USERNAME" -s enabled=True
/opt/keycloak/bin/kcadm.sh set-password --username "$USERNAME" --new-password "$PASSWORD"
/opt/keycloak/bin/kcadm.sh add-roles --uusername "$USERNAME" --rolename admin