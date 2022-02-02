from django.conf import settings
from cloudharness.middleware import update_state


class CloudharnessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        bearer = request.headers.get('Authorization')
        env = "production" if not settings.DEBUG else "development"
        update_state({
            "bearer": bearer,
            "env": env,
        })

        response = self.get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response
