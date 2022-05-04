from contextvars import ContextVar, copy_context

_authentication_token = ContextVar("ch_authentication_token", default=None)

def set_authentication_token(authentication_token):
    _authentication_token.set(authentication_token)

def get_authentication_token():
    return _authentication_token.get()
