FROM quay.io/keycloak/keycloak:16.1.0

# add kubectl
USER root
RUN cd /usr/local/bin && \
    curl -sSLO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl
COPY --chmod=0755 scripts/create_api_user.sh /opt/jboss/startup-scripts/create_api_user.sh
USER jboss

# Customize keycloak look
COPY themes/custom /opt/jboss/keycloak/themes/custom
