from contextvars import ContextVar, copy_context

_middleware = None
_state = ContextVar("ch_state", default={})

def update_state(state):
    new_state = _state.get()
    new_state.update(state)
    _state.set(new_state)

def get_state():
    return _state.get()
