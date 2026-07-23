from http.cookies import SimpleCookie

from cloudharness.middleware import set_authentication_token


class AuthMiddleware:
    '''
    CloudHarness ASGI middleware.

    Stores the request bearer token in a context variable so that the
    AuthClient can resolve the current user. Registered on the connexion
    application (which is ASGI based since connexion 3) via `add_middleware`;
    the token is set in the request context and propagates into the
    synchronous Flask handler (a2wsgi copies the context into its worker
    thread).
    '''

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] in ("http", "websocket"):
            set_authentication_token(self._extract_token(scope))
        await self.app(scope, receive, send)

    @staticmethod
    def _extract_token(scope):
        headers = {
            key.decode("latin-1").lower(): value.decode("latin-1")
            for key, value in scope.get("headers") or []
        }

        # Prefer the Authorization header, fall back to the kc-access cookie
        authorization = headers.get("authorization", "")
        if authorization:
            return authorization.split(" ")[-1] or None

        cookie_header = headers.get("cookie")
        if cookie_header:
            cookies = SimpleCookie()
            cookies.load(cookie_header)
            if "kc-access" in cookies:
                return cookies["kc-access"].value or None

        return None
