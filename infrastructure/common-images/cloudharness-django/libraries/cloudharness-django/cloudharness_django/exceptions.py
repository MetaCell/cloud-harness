from keycloak.exceptions import KeycloakOperationError


class KeycloakOIDCNoAdminRole(KeycloakOperationError):
    pass


class KeycloakOIDCNoDefaultUserRole(KeycloakOperationError):
    pass


class KeycloakOIDCNoProjectError(KeycloakOperationError):
    pass


class KeycloakOIDCAuthServiceNotInitError(KeycloakOperationError):
    pass


class KeycloakOIDUserServiceNotInitError(KeycloakOperationError):
    pass
