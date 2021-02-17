#!/usr/bin/env python3

import os
import logging

from flask_cors import CORS

import connexion

from common import encoder

connexion_app = connexion.App(__name__, specification_dir='./openapi/')
app = connexion_app.app
app.config.from_object(os.environ['APP_SETTINGS'])
app.json_encoder = encoder.JSONEncoder

with app.app_context():
    # setup logging
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    from .repository.db import open_db

    open_db(app)
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
    connexion_app.add_api('openapi.yaml',
                          arguments={'title': 'CH service API'},
                          pythonic_params=True)

    try:
        # init_app can be defined to add behaviours to the wsgi app
        from common import init_app

        init_app(app)
    except ImportError:
        pass


def main():
    connexion_app.run(port=8080)


if __name__ == '__main__':
    main()
