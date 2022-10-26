import os
import logging

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)

HERE = os.path.dirname(os.path.realpath(__file__))
