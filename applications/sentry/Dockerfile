ARG REGISTRY
ARG TAG=latest
FROM sentry:${TAG}

ADD sentryrunner.sh ./sentryrunner.sh
RUN chmod +x ./sentryrunner.sh

ENV SENTRY_REDIS_HOST=sentry-redis-svr
ENV SENTRY_REDIS_PORT=6379
ENV SENTRY_POSTGRES_HOST=sentry-postgres-svr
ENV SENTRY_POSTGRES_PORT=5432
ENV SENTRY_DB_NAME=sentry
ENV SENTRY_DB_USER=sentry
ENV SENTRY_DB_PASSWORD=secret
ENV SENTRY_EMAIL_HOST=sentry-postfix-svr
ENV SENTRY_ADMIN_USER=sentry
ENV SENTRY_ADMIN_PASSWORD=secret
ENV SENTRY_EMAIL_FROM=sentry

ENTRYPOINT ["./sentryrunner.sh"]
