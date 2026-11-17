from contextvars import ContextVar, copy_context

_authentication_token = ContextVar("ch_authentication_token", default=None)


def set_authentication_token(authentication_token):
    # always set, so that a token never outlives the request it came with
    _authentication_token.set(authentication_token or None)


def get_authentication_token():
    return _authentication_token.get()


def bearer_token(authorization_header: str):
    """Extract the token from an `Authorization: Bearer <token>` header value."""
    scheme, _, token = (authorization_header or "").partition(" ")
    if scheme.lower() != "bearer" or not token or token == "undefined":
        return None
    return token.strip()
