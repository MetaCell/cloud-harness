import urllib.request
import sys
import logging
import os

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

assert len(sys.argv) > 1, 'File path not specified'

file_path = sys.argv[1]

logging.info("Displaying content for file".format(file_path))
assert os.path.exists(file_path), file_path + " does not exist."
with open(file_path) as f:
    print(f.read())
