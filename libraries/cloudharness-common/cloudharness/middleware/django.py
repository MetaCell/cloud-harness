from cloudharness.middleware import set_authentication_token
from django.http.request import HttpRequest


class CloudharnessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request: HttpRequest):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        # retrieve the bearer token from the header
        # and save it for use in the AuthClient
        set_authentication_token(request.headers.get('Authorization', '').split(' ')[-1] or request.COOKIES.get('kc-access', None))

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
