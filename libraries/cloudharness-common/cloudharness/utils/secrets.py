import os

def get_secret(name: str) -> str:
    """
    Helper class for the CloudHarness application secrets

    The application secret will be read from the secret file
    
    Args:
        name (str): name of the secret
        key (str): name of the data key in the secret
    """
    try:
        secrets_path = '/opt/cloudharness/resources/secrets'
        with open(os.path.join(secrets_path, name)) as fh:
            return fh.read()
    except:
        # if no secrets folder or file exists
        return ''
