FROM alpine:3.8

ENV NAME keycloak-gatekeeper
ENV KEYCLOAK_VERSION 9.0.2
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

WORKDIR /opt
RUN echo "https://downloads.jboss.org/keycloak/$KEYCLOAK_VERSION/gatekeeper/$NAME-$GOOS-$GOARCH.tar.gz"
RUN curl -fssL "https://downloads.jboss.org/keycloak/$KEYCLOAK_VERSION/gatekeeper/$NAME-$GOOS-$GOARCH.tar.gz" | tar -xz && chmod +x /opt/$NAME

ENTRYPOINT [ "" ]
CMD [ "/bin/sh", "-c", "sleep 10 && echo hello there && update-ca-certificates --verbose && /opt/keycloak-gatekeeper"]