#! /bin/bash

/opt/keycloak/bin/kc.sh $@ &

until /opt/keycloak/bin/kcadm.sh config credentials \
    --server http://localhost:8080 \
    --realm master \
    --user "$KC_BOOTSTRAP_ADMIN_USERNAME" \
    --password "$KC_BOOTSTRAP_ADMIN_PASSWORD";
do
    sleep 1s
done

for script in /opt/keycloak/startup-scripts/*.sh;
do
    bash "$script";
done

wait