#! /bin/bash

/opt/keycloak/bin/kc.sh $@ &

MAX_ATTEMPTS=30
ATTEMPT=0
API_USERNAME="admin_api"
API_PASSWORD=$(cat /opt/cloudharness/resources/auth/api_user_password 2>/dev/null || echo "")

echo "Waiting for Keycloak to start..."

# Wait for Keycloak to be ready
until curl -sf http://localhost:8080/health/ready > /dev/null 2>&1; do
    ATTEMPT=$((ATTEMPT + 1))
    if [ $ATTEMPT -ge $MAX_ATTEMPTS ]; then
        echo "ERROR: Keycloak did not become ready after $MAX_ATTEMPTS attempts."
        wait
        exit 1
    fi
    sleep 2s
done

echo "Keycloak is ready. Attempting authentication..."

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