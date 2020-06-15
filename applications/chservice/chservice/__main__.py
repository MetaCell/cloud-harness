import os

from flask import Flask

import connexion

from chservice import encoder

def main():
    app = connexion.App(__name__, specification_dir='./openapi/')
    app.app.config.from_object(os.environ['APP_SETTINGS'])
    app.app.json_encoder = encoder.JSONEncoder
    app.add_api('openapi.yaml',
                arguments={'title': 'CH service API'},
                pythonic_params=True)
    from .repository.db import open_db
    open_db(app)
    app.run(port=8080)

if __name__ == '__main__':
    main()
