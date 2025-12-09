#!/bin/bash


API_USERNAME="admin_api"
API_PASSWORD=$(cat /opt/cloudharness/resources/auth/api_user_password 2>/dev/null || echo "")

echo "create_api_user: waiting for Keycloak to start..."

# Wait for Keycloak to be ready - just give it some time to start up
sleep 120s

echo "Attempting authentication..."

# First, try to authenticate as admin_api
if [ -n "$API_PASSWORD" ] && /opt/keycloak/bin/kcadm.sh config credentials \
    --server http://localhost:8080 \
    --realm master \
    --user "$API_USERNAME" \
    --password "$API_PASSWORD" 2>/dev/null; then
    echo "Successfully authenticated as $API_USERNAME"
    echo "Startup scripts not needed (admin_api user already exists)"
else
    echo "admin_api user does not exist or authentication failed. Authenticating as bootstrap admin to create the user..."
    
    # Authenticate as bootstrap admin to create admin_api user
    if ! /opt/keycloak/bin/kcadm.sh config credentials \
        --server http://localhost:8080 \
        --realm master \
        --user "$KC_BOOTSTRAP_ADMIN_USERNAME" \
        --password "$KC_BOOTSTRAP_ADMIN_PASSWORD"; then
        echo "ERROR: Failed to authenticate as bootstrap admin. You must manually create the ${API_USERNAME} with password from the secret api_user_password."
        echo "Continuing without running startup scripts..."
        exit 0
    fi
    
    echo "Successfully authenticated as bootstrap admin"

    echo "Checking if API user exists..."

    # Check if user already exists
    if /opt/keycloak/bin/kcadm.sh get users -q "username=$API_USERNAME" | grep -q "$API_USERNAME"; then
        echo "ERROR: API user $API_USERNAME already exists, but password is out of sync. You may need to reset it manually."
        # /opt/keycloak/bin/kcadm.sh set-password --username "$API_USERNAME" --new-password "$API_PASSWORD"
        # Removed automatic password reset as that would only work if the main admin password is unchanged from the default password
        # That would create the false impression that the password is reset successfully when in fact it has not on production systems
        exit 0
    fi

    echo "Creating API user $API_USERNAME"
    set -e 
    # create the user and reload keycloak
    /opt/keycloak/bin/kcadm.sh create users -s "username=$API_USERNAME" -s enabled=True
    /opt/keycloak/bin/kcadm.sh set-password --username "$API_USERNAME" --new-password "$API_PASSWORD"
    /opt/keycloak/bin/kcadm.sh add-roles --uusername "$API_USERNAME" --rolename admin

    echo "API user created successfully"
fi   

