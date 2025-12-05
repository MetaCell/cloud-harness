#!/bin/bash

NAMESPACE=${CH_ACCOUNTS_REALM}
USERNAME=admin_api
PASSWORD=$(cat /opt/cloudharness/resources/auth/api_user_password)

echo "Checking if API user exists..."

# Check if user already exists
if /opt/keycloak/bin/kcadm.sh get users -q "username=$USERNAME" | grep -v "$USERNAME"; then
    # create the user and reload keycloak
    echo "Creating API user $USERNAME"
    /opt/keycloak/bin/kcadm.sh create users -s "username=$USERNAME" -s enabled=True
    echo "API user created successfully"
fi

echo Setting API user password
/opt/keycloak/bin/kcadm.sh set-password --username "$USERNAME" --new-password "$PASSWORD"
/opt/keycloak/bin/kcadm.sh add-roles --uusername "$USERNAME" --rolename admin
