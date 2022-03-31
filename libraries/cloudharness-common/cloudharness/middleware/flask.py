from werkzeug.wrappers import Request, Response, ResponseStream
from cloudharness.middleware import set_authentication_token


class middleware():
    '''
    CloudHarness WSGI middleware
    '''

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        request = Request(environ)

        # retrieve the bearer token from the header
        # and save it for use in the AuthClient
        set_authentication_token(request.headers.get('Authorization'))

        return self.app(environ, start_response)
