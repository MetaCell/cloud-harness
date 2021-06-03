#!/bin/bash

echo "**** S:INI ****"
export SENTRY_SECRET_KEY=$(sentry config generate-secret-key)

export SENTRY_SERVER_EMAIL=`cat /opt/cloudharness/resources/secrets/email-server`
if [ -z "${SENTRY_SERVER_EMAIL}" ]; then
  export SENTRY_SERVER_EMAIL=${SENTRY_EMAIL_FROM}@${DOMAIN}
fi

export SENTRY_EMAIL_USER=`cat /opt/cloudharness/resources/secrets/email-user`
export SENTRY_EMAIL_PASSWORD=`cat /opt/cloudharness/resources/secrets/email-password`

# create / update database
set -e

sentry upgrade --noinput   
echo "**** E:INI ****"

echo "**** S:CEL ****"
# start celery
sleep 10
export C_FORCE_ROOT=1
nohup sentry run cron 2>&1 > /var/log/sentrycron.log &
nohup sentry run worker 2>&1 > /var/log/sentryworker.log &
echo "**** E:CEL ****"

echo "**** S:USR ****"
# create superuser if not exists
set +e
sentry exec -c "
from sentry.models import User
try:
    user=User.objects.all()[0]
except IndexError:
    # no user found
    quit(1)
quit(0)
"
userExists=$?
set -e

if [ $userExists -eq 1 ]; then
sleep 15
echo creating new user
sentry createuser --email ${SENTRY_ADMIN_USER}@${DOMAIN} --password ${SENTRY_ADMIN_PASSWORD} --superuser --no-input
fi
echo "**** E:USR ****"

echo "**** S:RUN ****"
# run sentry
sentry run web
echo "**** E:RUN ****"