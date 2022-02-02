from flask import current_app
from werkzeug.wrappers import Request, Response, ResponseStream
from cloudharness.middleware import update_state


class middleware():
    '''
    CloudHarness WSGI middleware
    '''

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request = Request(environ)
        bearer = request.headers.get("Authorization")
        try:
            env = current_app.config.get("ENV")
        except:
            env = "production"
        update_state({
            "bearer": bearer,
            "env": env,
        })

        return self.app(environ, start_response)
