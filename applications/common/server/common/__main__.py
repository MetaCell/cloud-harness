#!/usr/bin/env python3

from cloudharness.utils.server import init_flask, main
from flask_cors import CORS
from common.repository.db import open_db

def init_fn(app):
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
    open_db(app)

app = init_flask(init_app_fn=open_db)

if __name__ == '__main__':
    main()
