FROM quay.io/keycloak/keycloak:26.0

EXPOSE 9000

USER root
COPY --chmod=0755 scripts/create_api_user.sh /opt/keycloak/startup-scripts/create_api_user.sh
COPY --chmod=0755 scripts/kc-entrypoint.sh /opt/keycloak/bin/kc-entrypoint.sh

USER keycloak

# Customize keycloak look
COPY themes/custom /opt/keycloak/themes/custom

# # keycloak kafka listener plugin
# COPY plugins/metacell-admin-event-listener-bundle-1.0.0.ear /opt/jboss/keycloak/standalone/deployments/

ENTRYPOINT [ "/opt/keycloak/bin/kc-entrypoint.sh" ]
CMD [ "start-dev", "--import-realm", "--health-enabled=true" ]