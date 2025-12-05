#! /bin/bash

/opt/keycloak/bin/kc.sh $@ &

API_USERNAME="admin_api"
API_PASSWORD=$(cat /opt/cloudharness/resources/auth/api_user_password 2>/dev/null || echo "")

echo "Waiting for Keycloak to start..."

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
    echo "admin_api user does not exist or authentication failed. Authenticating as bootstrap admin to create/update the user..."
    
    # Authenticate as bootstrap admin to create admin_api user
    if ! /opt/keycloak/bin/kcadm.sh config credentials \
        --server http://localhost:8080 \
        --realm master \
        --user "$KC_BOOTSTRAP_ADMIN_USERNAME" \
        --password "$KC_BOOTSTRAP_ADMIN_PASSWORD"; then
        echo "ERROR: Failed to authenticate as bootstrap admin. Check KC_BOOTSTRAP_ADMIN credentials."
        echo "Continuing without running startup scripts..."
        wait
        exit 0
    fi
    
    echo "Successfully authenticated as bootstrap admin"
    
    # Run startup scripts to create admin_api user
    for script in /opt/keycloak/startup-scripts/*.sh;
    do
        echo "Running startup script: $script"
        if bash "$script"; then
            echo "Successfully executed $script"
        else
            echo "Warning: $script failed with exit code $?"
        fi
    done
fi

wait