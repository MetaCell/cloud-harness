#!/bin/bash

NAMESPACE=${CH_ACCOUNTS_REALM}
USERNAME=admin_api
PASSWORD=$(echo $RANDOM | md5sum | head -c 20; echo;)

api_user_secret_exists=$(kubectl -n ${NAMESPACE} get secret accounts-api >/dev/null; echo $?)

if [ "${api_user_secret_exists}" -ne "0" ];
then
set -e
echo Creating API user

# create the user and reload keycloak
/opt/jboss/keycloak/bin/add-user-keycloak.sh -u ${USERNAME} -p ${PASSWORD}

kubectl create secret generic -n ${NAMESPACE} accounts-api \
  --from-literal=api_user_username=$(echo -n "${USERNAME}" | tr -d '\n') \
  --from-literal=api_user_password=$(echo -n "${PASSWORD}" | tr -d '\n')

fi
