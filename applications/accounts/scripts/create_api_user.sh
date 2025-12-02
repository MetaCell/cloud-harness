#!/bin/bash

NAMESPACE=${CH_ACCOUNTS_REALM}
USERNAME=admin_api
PASSWORD=$(cat /opt/cloudharness/resources/auth/api_user_password)

# create the user and reload keycloak
echo Creating API user
/opt/keycloak/bin/kcadm.sh create users -s "username=$USERNAME" -s enabled=True

echo Setting API user password
/opt/keycloak/bin/kcadm.sh set-password --username "$USERNAME" --new-password "$PASSWORD"

echo Adding API user to admin role
/opt/keycloak/bin/kcadm.sh add-roles --uusername "$USERNAME" --rolename admin