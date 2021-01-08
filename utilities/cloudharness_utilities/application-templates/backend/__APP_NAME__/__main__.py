#!/usr/bin/env python3

import atexit
import logging

import connexion
from flask import request
from __APP_NAME__ import encoder


# setup connection app
connexion_app = connexion.App(__name__, specification_dir="./openapi/")
app = connexion_app.app
app.json_encoder = encoder.JSONEncoder

with app.app_context():
    # setup logging
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    connexion_app.add_api("openapi.yaml", arguments={"title": "__APP_NAME__"}, pythonic_params=True)

    try:
        # init_app can be defined to add behaviours to the wsgi app
        from __APP_NAME__ import init_app
        init_app(app)
    except ImportError:
        pass


def main():
    connexion_app.run()


if __name__ == "__main__":
    main()
