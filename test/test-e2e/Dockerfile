FROM ghcr.io/puppeteer/puppeteer:24

USER root
RUN mkdir -p /home/test
RUN  chown -R pptruser /home/test
WORKDIR /home/test
# Install Chrome for the root user: Codefresh runs the container as root
RUN npx puppeteer browsers install chrome 

USER pptruser
COPY package.json . 
COPY yarn.lock . 
RUN yarn install --timeout 99999999

COPY --chown=pptruser . . 
ENV APP_URL=https://github.com

CMD ["yarn", "test"]