import os

def get_secret(name: str, key: str):
    """
    Helper class for the CloudHarness application secrets

    The application secret will be read from the secret file
    
    Args:
        name (str): name of the secret
        key (str): name of the data key in the secret
    """
    return os.environ.get(f'{name}-{key}', None)
