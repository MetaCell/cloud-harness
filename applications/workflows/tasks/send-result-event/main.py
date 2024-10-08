import sys
import os

import glob
from cloudharness import log, set_debug
from cloudharness.workflows.utils import notify_queue


from cloudharness.events.client import EventClient
from cloudharness.workflows.utils import get_workflow_name

MAX_FILE_SIZE = 2 ** 20  # 1MB
print("Starting send-result-event")
set_debug()


topic_name = get_workflow_name()  # Coming from the workflow name

log.info("Topic name is: " + topic_name)

assert len(sys.argv) > 1, 'Specify read path'


shared_directory = sys.argv[1]

log.info("Sending content of directory `{}` to event queue topic `{}`".format(shared_directory, topic_name))


assert os.path.exists(shared_directory), shared_directory + " does not exist."

for file_path in glob.glob(f"{shared_directory}/*"):
    log.info("File `{}`".format(file_path))
    size = os.path.getsize(file_path)
    if size > MAX_FILE_SIZE:
        log.warning(f"{file_path} size is {size}, which is greater than the maximum of {MAX_FILE_SIZE}."
                    "The content will not be sent to the queue")
        notify_queue(topic_name, {file_path: "Error: size exceeded"})

    log.info("Sending content for file `{}`".format(file_path))
    try:
        with open(file_path) as f:
            content = f.read()
    except Exception as e:
        log.error("Error reading file " + file_path + " " + str(e))
        continue

    notify_queue(topic_name, {os.path.basename(file_path): content})
