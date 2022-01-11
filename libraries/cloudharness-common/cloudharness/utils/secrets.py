import os

SECRETS_PATH = os.getenv("CH_SECRETS_PATH", "/opt/cloudharness/resources/secrets")


class SecretNotFound(Exception):
    def __init__(self, secret_name):
        Exception.__init__(self, f"Secret {secret_name} not found.")


def get_secret(name: str) -> str:
    """
    Helper class for the CloudHarness application secrets

    The application secret will be read from the secret file
    
    Args:
        name (str): name of the secret
        key (str): name of the data key in the secret
    """
    try:
        with open(os.path.join(SECRETS_PATH, name)) as fh:
            return fh.read()
    except:
        # if no secrets folder or file exists
        raise SecretNotFound(name)
