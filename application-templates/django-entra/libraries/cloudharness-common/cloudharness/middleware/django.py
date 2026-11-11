from cloudharness.middleware import bearer_token, set_authentication_token
from django.http.request import HttpRequest


class CloudharnessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request: HttpRequest):
        # retrieve the bearer token from the header
        # and save it for use in the auth helpers
        set_authentication_token(bearer_token(request.headers.get('Authorization', '')))

        return self.get_response(request)
