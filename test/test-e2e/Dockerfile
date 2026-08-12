FROM ghcr.io/puppeteer/puppeteer:24

USER root
RUN mkdir -p /home/test
RUN  chown -R pptruser /home/test
WORKDIR /home/test
# Install Chrome for the root user: Codefresh runs the container as root
RUN npx puppeteer browsers install chrome

# Same yarn setup as the cloudharness-frontend-build base image, repeated here because
# this image has to derive from the puppeteer runtime instead. The bundled classic yarn
# (1.22) has no release-age gate; that setting needs yarn >= 4.10.
# COREPACK_HOME is shared so the yarn fetched as root stays usable after USER pptruser.
ENV COREPACK_ENABLE_DOWNLOAD_PROMPT=0
ENV COREPACK_HOME=/usr/local/corepack
RUN corepack enable && corepack prepare yarn@4.18.0 --activate && chmod -R a+rX ${COREPACK_HOME}
ENV YARN_NODE_LINKER=node-modules
ENV YARN_NPM_MINIMAL_AGE_GATE=7d
# Replaces the former `yarn install --timeout 99999999`, which yarn 4 rejects.
ENV YARN_HTTP_TIMEOUT=99999999

USER pptruser
COPY --chown=pptruser package.json .
COPY --chown=pptruser yarn.lock .
RUN yarn install --immutable

COPY --chown=pptruser . . 
ENV APP_URL=https://github.com

CMD ["yarn", "test"]