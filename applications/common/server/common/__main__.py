import os

from flask import Flask
from flask_cors import CORS

import connexion

from common import encoder

def main():
    app = connexion.App(__name__, specification_dir='./openapi/')
    app.app.config.from_object(os.environ['APP_SETTINGS'])
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('openapi.yaml',
                arguments={'title': 'CH service API'},
                pythonic_params=True)
    from .repository.db import open_db
    open_db(app)
    cors = CORS(app.app, resources={r"/api/*": {"origins": "*"}})
    app.run(port=8080)

if __name__ == '__main__':
    main()
