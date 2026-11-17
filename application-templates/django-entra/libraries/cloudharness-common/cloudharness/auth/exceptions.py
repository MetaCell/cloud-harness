class InvalidToken(Exception):
    pass


class EntraNotConfigured(Exception):
    def __init__(self):
        Exception.__init__(
            self,
            "Entra is not configured: set entra.tenant_id and entra.client_id in the application values.yaml "
            "or the ENTRA_TENANT_ID and ENTRA_CLIENT_ID environment variables.")


class AuthSecretNotFound(Exception):
    def __init__(self, secret_name):
        Exception.__init__(self, f"Secret {secret_name} not found.")
