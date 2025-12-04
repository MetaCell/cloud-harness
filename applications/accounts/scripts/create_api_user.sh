#!/bin/bash

NAMESPACE=${CH_ACCOUNTS_REALM}
USERNAME=admin_api
PASSWORD=$(cat /opt/cloudharness/resources/auth/api_user_password)

set -e
echo "Checking if API user exists..."

# Check if user already exists
if /opt/keycloak/bin/kcadm.sh get users -q "username=$USERNAME" | grep -q "$USERNAME"; then
    echo "API user $USERNAME already exists, skipping creation"
    exit 0
fi

echo "Creating API user $USERNAME"

# create the user and reload keycloak
/opt/keycloak/bin/kcadm.sh create users -s "username=$USERNAME" -s enabled=True
/opt/keycloak/bin/kcadm.sh set-password --username "$USERNAME" --new-password "$PASSWORD"
/opt/keycloak/bin/kcadm.sh add-roles --uusername "$USERNAME" --rolename admin

echo "API user created successfully"