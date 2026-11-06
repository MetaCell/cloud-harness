from cloudharness.middleware import bearer_token, set_authentication_token


class AuthMiddleware:
    '''
    CloudHarness ASGI middleware.

    Stores the request bearer token in a context variable so that the
    auth helpers can resolve the current user.
    '''

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            set_authentication_token(self._extract_token(scope))
        await self.app(scope, receive, send)

    @staticmethod
    def _extract_token(scope):
        for key, value in scope.get("headers") or []:
            if key.decode("latin-1").lower() == "authorization":
                return bearer_token(value.decode("latin-1"))
        return None
