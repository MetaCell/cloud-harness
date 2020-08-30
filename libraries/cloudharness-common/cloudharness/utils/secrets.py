import base64

def get_secret(secret_name: str):
    """
    Helper class for the CloudHarness application secrets

    The application secret will be read from the secret file
    
    """
    path = f"/opt/secrets/{secret_name}"
    with open(path, "r") as f:
        return base64.b64decode(f.readline()) ### ToDo: this should go into a secret !!!!
