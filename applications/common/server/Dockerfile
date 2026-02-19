ARG CLOUDHARNESS_FLASK

FROM $CLOUDHARNESS_FLASK

ENV MODULE_NAME=common

ENV WORKERS=2
ENV PORT=8080
RUN apt update && apt install -y postgresql

COPY ./requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

ENV FLASK_ENV=production
ENV APP_SETTINGS=common.config.ProductionConfig
RUN pip3 install -e /usr/src/app
