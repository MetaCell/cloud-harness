#!/usr/bin/env python3

from cloudharness.utils.server import init_flask, main
from cloudharness import log
from flask_cors import CORS
from common.repository.db import open_db
from common.controllers.sentry_controller import global_dsn


def init_fn(app):
    log.info("initializing database from app")
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
    if not global_dsn:
        open_db(app)


app = init_flask(init_app_fn=init_fn)

if __name__ == '__main__':
    main()
