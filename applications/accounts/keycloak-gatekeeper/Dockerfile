FROM alpine:3.8

ENV NAME keycloak-gatekeeper
ENV KEYCLOAK_VERSION 6.0.1
ENV GOOS linux
ENV GOARCH amd64
ENV DOMAIN cloudharness.local

LABEL Name=keycloak-gatekeeper \
      Release=https://github.com/keycloak/keycloak-gatekeeper \
      Url=https://github.com/keycloak/keycloak-gatekeeper \
      Help=https://issues.jboss.org/projects/KEYCLOAK

RUN apk add --no-cache curl tar bash
RUN apk add --update openssl && \
    rm -rf /var/cache/apk/*

RUN openssl genrsa -des3 -passout pass:x -out server.pass.key 2048 && \
    openssl rsa -passin pass:x -in server.pass.key -out server.key && \
    rm server.pass.key && \
    openssl req -new -key server.key -out server.csr \
        -subj "/C=UK/ST=Oxford/L=Leamington/O=OrgName/OU=IT Department/CN=*.${DOMAIN}" && \
    openssl x509 -req -days 365 -in server.csr -signkey server.key -out /usr/local/share/ca-certificates/cacert.crt
RUN cat /usr/local/share/ca-certificates/cacert.crt
WORKDIR /opt
RUN echo "https://downloads.jboss.org/keycloak/$KEYCLOAK_VERSION/gatekeeper/$NAME-$GOOS-$GOARCH.tar.gz"
RUN curl -fssL "https://downloads.jboss.org/keycloak/$KEYCLOAK_VERSION/gatekeeper/$NAME-$GOOS-$GOARCH.tar.gz" | tar -xz && chmod +x /opt/$NAME


# Update the CA list for ubuntu
RUN update-ca-certificates --verbose
# include your CA in httplib2 (required for hand-shake between UI servers and keycloak)
# RUN cat /usr/local/share/ca-certificates/extra/cacert.crt >> /usr/local/lib/python3.7/site-packages/certifi/cacert.pem

####

ENTRYPOINT [ "/opt/keycloak-gatekeeper" ]