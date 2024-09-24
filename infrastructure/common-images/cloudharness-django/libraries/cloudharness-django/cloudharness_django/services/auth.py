import os
import time
from enum import Enum
from typing import List

from keycloak.exceptions import KeycloakGetError, KeycloakError

from cloudharness import log
from cloudharness.auth import AuthClient, get_auth_realm
from cloudharness.utils.config import ALLVALUES_PATH

from cloudharness_django.exceptions import KeycloakOIDCNoAdminRole


class AuthorizationLevel(Enum):
    NO_AUTHORIZATION = 1
    NON_PRIVILEGED = 2
    PRIVILEGED = 3
    ADMIN = 4


# create the auth client
if os.path.isfile(ALLVALUES_PATH):
    try:
        # CH values exists so running with a valid config
        auth_client = AuthClient(os.getenv("ACCOUNTS_ADMIN_USERNAME", None), os.getenv("ACCOUNTS_ADMIN_PASSWORD", None))
    except:
        log.exception("Failed to initialize auth client")
        auth_client = None
else:
    auth_client = None


class AuthService:

    def __init__(
        self,
        client_name: str,
        client_roles: List[str],
        privileged_roles: List[str],
        admin_role: str,
        default_user_role: str = None,
    ):
        if not admin_role:
            raise KeycloakOIDCNoAdminRole("No admin role given.")
        self.client_name = client_name
        self.client_roles = client_roles
        self.default_user_role = default_user_role
        self.privileged_roles = privileged_roles
        self.admin_role = admin_role

    @classmethod
    def get_auth_client(cls):
        return auth_client

    def get_client_name(self):
        return self.client_name

    def get_admin_role(self):
        return self.admin_role

    def create_client(self):
        """
        Create the client and client roles
        Checks if the client is present, if not the creates it
        """

        try:
            auth_client.refresh_token()
            try:
                client = auth_client.get_client(self.get_client_name())
            except KeycloakGetError as e:
                # thrown if client doesn't exist
                auth_client.create_client(client_name=self.get_client_name())
                client = auth_client.get_client(self.get_client_name())

            for role in self.client_roles:
                try:
                    log.info("Creating role %s", role)
                    auth_client.create_client_role(client["id"], role)
                except KeycloakError as e:
                    # Thrown if role already exists
                    log.error(e.error_message)

            if self.default_user_role:
                # add the default user role to the default realm role
                realm = get_auth_realm()
                admin_client = auth_client.get_admin_client()
                admin_client.refresh_token()
                default_user_role = admin_client.get_client_role(
                    self.get_client_name(),
                    self.default_user_role
                )
                admin_client.add_composite_realm_roles_to_role(
                    f'default-roles-{realm}',
                    [default_user_role, ]
                )
        except Exception as e:
            log.error("Error creating Keycloak client %s. May need to manually migrate the client.", self.get_client_name(), exc_info=True)
            raise Exception("Error creating Keycloak client.") from e

    def get_auth_level(self, kc_user=None, kc_roles=None):
        if not kc_user:
            kc_user = auth_client.get_current_user()

        if not kc_roles:
            kc_roles = auth_client.get_user_client_roles(
                kc_user.get("id"),
                self.get_client_name()
            )
        assigned_roles = [r["name"] for r in kc_roles]

        admin = self.admin_role in assigned_roles
        if admin:
            return AuthorizationLevel.ADMIN

        privileged = any(
            [role in assigned_roles for role in self.privileged_roles])
        if privileged:
            return AuthorizationLevel.PRIVILEGED

        non_privileged = any(
            [role in assigned_roles for role in self.client_roles])
        if non_privileged:
            return AuthorizationLevel.NON_PRIVILEGED

        return AuthorizationLevel.NO_AUTHORIZATION
