ARG CLOUDHARNESS_BASE

FROM $CLOUDHARNESS_BASE

ENV MODULE_NAME=notifications

COPY pylock.toml /usr/src/app/

WORKDIR /usr/src/app

RUN pip3 install --no-cache-dir -r pylock.toml

COPY . /usr/src/app

RUN pip install --uploaded-prior-to=P7D -e .

ENTRYPOINT python3 -m notifications
