from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError


class UserNotFound(KeycloakGetError):
    pass


class InvalidToken(Exception):
    pass


class AuthSecretNotFound(Exception):
    def __init__(self, secret_name):
        Exception.__init__(self, f"Secret {secret_name} not found.")
