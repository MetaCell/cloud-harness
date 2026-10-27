import os
from os.path import dirname as dn
import logging

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler()
    ]
)

HERE = os.path.dirname(os.path.realpath(__file__))


CH_ROOT = os.getenv("CH_ROOT") or dn(dn(dn(dn(os.path.realpath(__file__))))).replace(os.path.sep, '/')

# Imported for their @register_file side effect, not for re-export.
from . import codefresh, dockercompose, helm, report, skaffold, tilt, vscode  # noqa: F401,E402

try:
    import pyvis  # noqa: F401
except ImportError:
    pass
else:
    from . import diagram  # noqa: F401,E402

from .model import CHDeployConfig, CHProject  # noqa: E402

__all__ = [
    "CHDeployConfig",
    "CHProject",
]
