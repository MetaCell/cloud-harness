import sys
import os

from cloudharness import log

assert len(sys.argv) > 1, 'File path not specified'

file_path = sys.argv[1]

log.info("Displaying content for file".format(file_path))
assert os.path.exists(file_path), file_path + " does not exist."
with open(file_path) as f:
    print(f.read())
