#!/usr/bin/env python3

from cloudharness.utils.server import init_flask, main
from cloudharness import log
from common.repository.db import open_db
from common.controllers.sentry_controller import global_dsn


def init_fn(app):
    log.info("initializing database from app")
    # CORS is now handled by the init_flask function
    if not global_dsn:
        open_db(app)


app = init_flask(init_app_fn=init_fn)

if __name__ == '__main__':
    main()
