
import sys
import os
import logging

from cloudharness.workflows.utils import notify_queue

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

assert len(
    sys.argv) > 3, 'Not all arguments not specified. Cannot notify queue. Usage: [workflow status] [queue name] [payload]'


queue = sys.argv[2]
message = {'status': sys.argv[1], 'payload': sys.argv[3], 'workflow': os.getenv('CH_WORKFLOW_NAME')}
notify_queue(queue, message)
