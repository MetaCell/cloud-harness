import os
from os.path import dirname as dn
import logging

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)

HERE = os.path.dirname(os.path.realpath(__file__))


CH_ROOT = os.getenv("CH_ROOT") or dn(dn(dn(dn(os.path.realpath(__file__))))).replace(os.path.sep, '/')
