import flask
from flask_sqlalchemy import SQLAlchemy


def open_db():
    return SQLAlchemy(flask.current_app)
