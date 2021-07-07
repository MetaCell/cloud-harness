ARG CLOUDHARNESS_BASE

FROM $CLOUDHARNESS_BASE

ENV MODULE_NAME=notifications

COPY requirements.txt /usr/src/app/

WORKDIR /usr/src/app

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . /usr/src/app

RUN pip install -e .

ENTRYPOINT python3 -m notifications
