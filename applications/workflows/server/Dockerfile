ARG CLOUDHARNESS_FLASK

FROM $CLOUDHARNESS_FLASK

ENV MODULE_NAME=workflows_api

COPY ./requirements.txt /usr/src/app/

RUN --mount=type=cache,target=/root/.cache python -m pip install --upgrade pip &&\
    pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

EXPOSE 8080
RUN pip3 install -e .
