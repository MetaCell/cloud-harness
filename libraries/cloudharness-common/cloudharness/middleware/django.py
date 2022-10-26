from django.conf import settings
from cloudharness.middleware import set_authentication_token


class CloudharnessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        # retrieve the bearer token from the header
        # and save it for use in the AuthClient
        set_authentication_token(request.headers.get('Authorization'))

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
