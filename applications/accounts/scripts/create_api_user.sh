#!/bin/bash

NAMESPACE=${CH_ACCOUNTS_REALM}
USERNAME=admin_api
PASSWORD=$(cat /opt/cloudharness/resources/auth/api_user_password)

echo "Checking if API user exists..."

# Check if user already exists
if /opt/keycloak/bin/kcadm.sh get users -q "username=$USERNAME" | grep -q "$USERNAME"; then
    echo "ERROR: API user $USERNAME already exists, but password is out of sync. You may need to reset it manually."
    # /opt/keycloak/bin/kcadm.sh set-password --username "$USERNAME" --new-password "$PASSWORD"
    # Removed automatic password reset as that would only work if the main admin password is unchanged from the default password
    # That would create the false impression that the password is reset successfully when in fact it has not on production systems
    exit 0
fi

echo "Creating API user $USERNAME"
set -e 
# create the user and reload keycloak
/opt/keycloak/bin/kcadm.sh create users -s "username=$USERNAME" -s enabled=True
/opt/keycloak/bin/kcadm.sh set-password --username "$USERNAME" --new-password "$PASSWORD"
/opt/keycloak/bin/kcadm.sh add-roles --uusername "$USERNAME" --rolename admin

echo "API user created successfully"