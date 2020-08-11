import base64
import io
import json
import os
import urllib
import urllib.request

import jose.jwt
from oauthenticator.generic import GenericOAuthenticator
from tornado import gen
from tornado.httpclient import HTTPRequest, AsyncHTTPClient
from traitlets import Unicode, Dict, Set, observe


class KeyCloakAuthenticator(Authenticator):
    # There is only one authenticator instance

    admin_role = Unicode(
        config=True,
        help="Keycloak client role to grant admin access."
    )

    required_roles = Set(
        Unicode(),
        set(x.strip()
            for x in os.environ.get('OIDC_REQUIRED_ROLES', '').split(',')
            if x.strip()
            ),
        config=True,
        help="Required resource access roles. Any role is sufficient.",
    )

    oidc_config_url = Unicode(
        os.environ.get('OIDC_CONFIG_URL', ''),
        config=True,
        help="Well-Known openid configuration url"
    )

    oidc_config = Dict(
        config=False,
        help="OIDC config loaded from oidc_config_url"
    )

    oidc_issuer = Unicode(
        os.environ.get('OIDC_ISSUER', ''),
        config=False,
        help="OIDC Issuer. Used to validate tokens."
    )

    jwks = Dict(
        config=False,
        help="JWKS (key set) to validate OIDC tokens (derived from oidc_config)"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # initial load of oidc config
        self._load_oidc_config()

    def _load_oidc_config(self):
        with urllib.request.urlopen(self.oidc_config_url) as resp:
            self.oidc_config = json.load(
                io.TextIOWrapper(resp, 'utf-8', 'replace')
            )

    @observe('oidc_config')
    def _oidc_config_changed(self, change):
        # change['new'], ['old']
        self.oidc_issuer = self.oidc_config.get('issuer', '')
        self.userdata_url = self.oidc_config.get('userinfo_endpoint', '')
        self.token_url = self.oidc_config.get('token_endpoint', '')
        self.login_handler._OAUTH_AUTHORIZE_URL = self.oidc_config.get('authorization_endpoint', '')
        self.login_handler._OAUTH_ACCESS_TOKEN_URL = self.oidc_config.get('token_endpoint', '')
        with urllib.request.urlopen(self.oidc_config['jwks_uri']) as resp:
            self.jwks = json.load(io.TextIOWrapper(resp, 'utf-8', 'replace'))

    @gen.coroutine
    def pre_spawn_start(self, user, spawner):
        super().pre_spawn_start(user, spawner)

        auth_state = yield user.get_auth_state()
        if not auth_state:
            # auth_state not enabled
            return

        # spawner would have self.user, but there is no easy way to get
        # auth_state in spawner, as it is a coroutine, and everywhere
        # were we would need it it is either hard to inject env variables
        # or we can't call a coroutine.
        spawner.oauth_user = auth_state.get('oauth_user', {})

    def decode_jwt_token(self, token):
        try:
            return jose.jwt.decode(
                token, self.jwks,
                audience=self.client_id,
                issuer=self.oidc_issuer,
                # wo don't have at_hash in id_token, so we can't verify access_token here
                # access_token=access_token,
                options={
                    # verify audience only if we have no required roles
                    'verify_aud': not self.required_roles,
                }
            )
        except Exception as e:
            # TODO: log error?
            return

    def get_roles_from_token(self, token):
        return set(
            token.get('resource_access', {}).get(self.client_id, {}).get('roles', [])
        )

    def validate_roles(self, user_roles):
        return bool(not self.required_roles or (self.required_roles & user_roles))

    def get_user_for_token(self, access_token):
        # accepts access_token and returns user name
        token = self.decode_jwt_token(access_token)
        if not token:
            return None
        name = token.get(self.username_key, None)
        if not name:
            return None

        self.log.info('Token: %s', token)
        # get user roles from access token
        user_roles = self.get_roles_from_token(token)
        if not self.validate_roles(user_roles):
            return None
        is_admin = bool(self.admin_role and (self.admin_role in user_roles))
        return {
            'name': name,
            'admin': is_admin
        }

    @gen.coroutine
    def authenticate(self, handler, data=None):
        http_client = AsyncHTTPClient()
        # short circuit if we have a token in data:
        # see https://github.com/jupyterhub/jupyterhub/pull/1840
        if data and 'token' in data:
            # TODO: check roles?
            user = self.get_user_for_token(data['token'])
            if user is None:
                return None
            # ensure user exists in db
            userob = handler.user_from_username(user['name'])
            if userob is None:
                return None
            # This code path should only be reachable from UserTokenListAPIHandler
            # which currently only wants a username as return value
            return user['name']

        # trade authorization code for tokens
        code = handler.get_argument("code")
        params = dict(
            redirect_uri=self.get_callback_url(handler),
            code=code,
            scope='openid',
            grant_type='authorization_code'
        )
        params.update(self.extra_params)

        if self.token_url:
            url = self.token_url
        else:
            raise ValueError("Please set the OAUTH2_TOKEN_URL environment variable")

        b64key = base64.b64encode(
            bytes(
                "{}:{}".format(self.client_id, self.client_secret),
                "utf8"
            )
        )

        headers = {
            "Accept": "application/json",
            "User-Agent": "JupyterHub",
            "Authorization": "Basic {}".format(b64key.decode("utf8"))
        }
        req = HTTPRequest(
            url,
            method="POST",
            headers=headers,
            body=urllib.parse.urlencode(params)  # Body is required for a POST...
        )

        resp = yield http_client.fetch(req)

        resp_json = json.loads(resp.body.decode('utf8', 'replace'))

        # extract tokens
        access_token = resp_json['access_token']
        # expires_in: 300 ... access_token
        refresh_token = resp_json.get('refresh_token', None)
        # refresh_expires_in: 1800 ... refresh_token
        print(resp_json)
        id_token = resp_json['access_token']
        scope = (resp_json.get('scope', '')).split(' ')

        # verify id_token
        id_token = self.decode_jwt_token(id_token)
        if not (id_token and id_token.get(self.username_key)):
            self.log.error("OAuth user contains no key %s: %s", self.username_key, id_token)
            return

        # verify and decode access token
        user = self.get_user_for_token(access_token)
        if not user:
            return None

        # atok = self.decode_jwt_token(access_token)
        # if not atok:
        #     self.log.error("No Access Token")
        #     return
        # # get user roles from access token
        # user_roles = self.get_roles_from_token(atok)
        # user_name = id_token.get('name', id_token.get(self.username_key))

        # is_user = self.validate_roles(user_roles)
        # is_admin = bool(self.admin_role and (self.admin_role in user_roles))

        # if not is_user:
        #     self.log.error("User %s not allowed", user_name)
        #     return

        self.log.info('User {name} is admin: {admin}'.format(**user))
        # attach auth_state
        user['auth_state'] = {
            'access_token': access_token,
            'refresh_token': refresh_token,
            # 'id_token': id_token,
            'oauth_user': id_token,
            # 'oauth_roles': list(user_roles),
            'scope': scope,
        }
        return user
