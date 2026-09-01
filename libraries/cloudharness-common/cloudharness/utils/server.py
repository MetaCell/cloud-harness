"""Backwards compatibility: this module was renamed to `cloudharness.utils.flask_server`.

Aliasing through `sys.modules` rather than re-exporting keeps `cloudharness.utils.server`
and `cloudharness.utils.flask_server` the *same* module object, so module level state that
`init_flask` rebinds (notably `app`) stays visible through both names. A `__getattr__` on
the package cannot replace this file: PEP 562 covers attribute access, not the submodule
resolution that `from cloudharness.utils.server import init_flask` goes through.
"""
import sys

from . import flask_server

sys.modules[__name__] = flask_server
