#!/usr/bin/env python3

import logging

import connexion
from workflows_api import encoder

# setup connection app
connexion_app = connexion.App(__name__, specification_dir="./openapi/", debug=True)
app = connexion_app.app
app.json_encoder = encoder.JSONEncoder

with app.app_context():
    # setup logging
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    connexion_app.add_api("openapi.yaml", arguments={"title": "Workflows API"}, pythonic_params=True)
    try:
        # init_app can be defined to add behaviours to the wsgi app
        from workflows_api import init_app

        init_app(app)
    except ImportError:
        pass


def main():
    connexion_app.debug = True
    connexion_app.run(port=5000)


if __name__ == "__main__":
    main()
