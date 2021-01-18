#!/usr/bin/env python3

import logging

import connexion
import flask
from samples import encoder


# setup connection app
connexion_app = connexion.App(__name__, specification_dir="./openapi/", debug=True)
app = connexion_app.app
app.json_encoder = encoder.JSONEncoder

with app.app_context():
    # setup logging
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

    connexion_app.add_api("openapi.yaml", arguments={"title": "samples"}, pythonic_params=True)
    try:
        # init_app can be defined to add behaviours to the wsgi app
        from samples import init_app
        init_app(app)
    except ImportError:
        pass

@app.route('/', methods=['GET'])
def index():
    return flask.send_from_directory('../www', 'index.html')

@app.route('/<path:path>')
def send_webapp(path):
    return flask.send_from_directory('../www', path)

@app.route('/static/<path:path>')
def send_static(path):
    return flask.send_from_directory('../www/static', path)

def main():
    connexion_app.debug=True
    connexion_app.run(port=5001)


if __name__ == "__main__":
    main()
