#!/bin/bash

export API_USERNAME="admin_api"
export API_PASSWORD=$(cat /opt/cloudharness/resources/auth/api_user_password 2>/dev/null || echo "")
export TMP_CLIENT="tmp_api_client"
export TMP_CLIENT_SECRET="${KC_BOOTSTRAP_ADMIN_USERNAME}"

check_kc_ready() {
    if echo >/dev/tcp/127.0.0.1/${ACCOUNTS_SERVICE_PORT}; then
        return 0
    fi 2> /dev/null
    return 1
}

while ! check_kc_ready; do
    echo "create_api_user: waiting for Keycloak to be ready..."
    sleep 10
done

create_temporary_client() {
    /opt/keycloak/bin/kc.sh bootstrap-admin service --client-id=${TMP_CLIENT} --client-secret:env=TMP_CLIENT_SECRET --http-management-port 9876
}

delete_temporary_client() {
    CLIENT_ID=$(/opt/keycloak/bin/kcadm.sh get clients -r master -q clientId=${TMP_CLIENT} --fields id --format csv|tr -d '"')
    if [ -n "$CLIENT_ID" ]; then
        /opt/keycloak/bin/kcadm.sh delete clients/$CLIENT_ID -r master
    fi
}

create_kc_config() {
    /opt/keycloak/bin/kcadm.sh config credentials --server http://localhost:${ACCOUNTS_SERVICE_PORT} --realm master --client ${TMP_CLIENT} --secret ${TMP_CLIENT_SECRET}
}

api_user_exists() {
    return $(/opt/keycloak/bin/kcadm.sh get users -q "username=$API_USERNAME" | grep -q "$API_USERNAME"; echo $?)
}   

create_api_user() {
    /opt/keycloak/bin/kcadm.sh create users -s "username=${API_USERNAME}" -s enabled=True
}

set_password_and_roles() {
    /opt/keycloak/bin/kcadm.sh set-password --username "$API_USERNAME" --new-password "$API_PASSWORD"
    /opt/keycloak/bin/kcadm.sh add-roles --uusername "$API_USERNAME" --rolename admin
}

# Wait for Keycloak to be ready - just give it some time to start up


echo "create_api_user: attempting authentication..."

# First, try to authenticate as admin_api
if [ -n "$API_PASSWORD" ] && /opt/keycloak/bin/kcadm.sh config credentials \
    --server http://localhost:${ACCOUNTS_SERVICE_PORT} \
    --realm master \
    --user "$API_USERNAME" \
    --password "$API_PASSWORD" 2>/dev/null; then
    echo "create_api_user: successfully authenticated as $API_USERNAME"
    echo "create_api_user: sStartup scripts not needed (admin_api user already exists)"
    exit 0
fi

echo "create_api_user: admin_api user does not exist or authentication failed. Authenticating to create the user..."

set -e
create_temporary_client
create_kc_config
echo "create_api_user: temporary credentials successfully created."

echo "create_api_user: checking if API user exists..."
# Check if user already exists
if ! api_user_exists; then
    echo "create_api_user: API user $API_USERNAME doesn't exists, creating..."
    create_api_user
    echo "create_api_user: API user created successfully"
else
    echo "create_api_user: API user $API_USERNAME already exists."
fi

echo "create_api_user: setting password and role."
set_password_and_roles

echo "create_api_user: cleaning up temporary client."
delete_temporary_client
