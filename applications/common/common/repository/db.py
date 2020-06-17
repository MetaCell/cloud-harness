from flask_sqlalchemy import SQLAlchemy

db = None

def get_db():
    global db
    if not db:
        raise Exception('Database not open!')
    return db

def open_db(app):
    global db
    if not db:
        db = SQLAlchemy(app.app)
    return db
