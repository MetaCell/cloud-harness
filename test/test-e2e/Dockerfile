FROM ghcr.io/puppeteer/puppeteer:22

USER root
# If running Docker >= 1.13.0 use docker run's --init arg to reap zombie processes, otherwise
# uncomment the following lines to have `dumb-init` as PID 1
# ADD https://github.com/Yelp/dumb-init/releases/download/v1.2.2/dumb-init_1.2.2_x86_64 /usr/local/bin/dumb-init
# RUN chmod +x /usr/local/bin/dumb-init
# ENTRYPOINT ["dumb-init", "--"]

# Uncomment to skip the chromium download when installing puppeteer. If you do,
# you'll need to launch puppeteer with:
#     browser.launch({executablePath: 'google-chrome-stable'})
# ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD true
RUN mkdir -p /home/test
RUN groupadd -r test && useradd -r -g test -G audio,video test \
    && chown -R test:test /home/test
WORKDIR /home/test
USER test
COPY package.json . 
COPY yarn.lock . 
RUN yarn install --timeout 99999999


# Run everything after as non-privileged user.

RUN npx puppeteer browsers install chrome
COPY --chown=test . . 
USER test
CMD ["yarn", "test"]