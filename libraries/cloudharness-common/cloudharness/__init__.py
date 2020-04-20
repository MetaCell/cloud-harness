import logging
import sys

log = logging

# logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def set_debug():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)




__all__ = ['log']

# TODO log will write through a rest service
