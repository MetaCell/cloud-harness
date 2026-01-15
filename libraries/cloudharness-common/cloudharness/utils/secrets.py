import os
from cloudharness.utils.config import CloudharnessConfig

SECRETS_PATH = os.getenv("CH_SECRETS_PATH", "/opt/cloudharness/resources/secrets")


class SecretNotFound(Exception):
    def __init__(self, secret_name, app_name=None):
        if app_name:
            Exception.__init__(self, f"Secret {secret_name} not found for app {app_name}.")
        else:
            Exception.__init__(self, f"Secret {secret_name} not found.")


def get_secret(name: str, app_name: str = None) -> str:
    """
    Helper class for the CloudHarness application secrets

    The application secret will be read from the secret file

    Args:
        name (str): name of the secret
        app_name (str): name of the application (or dependency). Defaults to current app name.
    """
    if app_name is None:
        app_name = CloudharnessConfig.get_current_app_name()

    try:
        with open(os.path.join(SECRETS_PATH, app_name, name)) as fh:
            return fh.read()
    except:
        # if no secrets folder or file exists
        raise SecretNotFound(name, app_name)
