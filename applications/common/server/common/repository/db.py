from flask_sqlalchemy import SQLAlchemy
from cloudharness import log

db = None


def get_db():
    global db
    if not db:
        raise Exception('Database not open!')
    return db


def open_db(app):
    global db
    try:
        if not db:
            db = SQLAlchemy(app)
    except Exception as e:
        log.exception("Sentry database cannot be initialized")
    return db
