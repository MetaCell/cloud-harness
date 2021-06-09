ARG CLOUDHARNESS_BASE
FROM $CLOUDHARNESS_BASE

ADD . /

ENV workflow_result 'Failure'
ENV queue_name 'None'
ENV payload '{}'

CMD python main.py ${workflow_result} ${queue_name} ${payload}
