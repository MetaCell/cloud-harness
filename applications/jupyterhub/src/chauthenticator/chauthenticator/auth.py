import os
import sys
import logging

from jupyterhub.auth import Authenticator
from jupyterhub.handlers import BaseHandler
from tornado import gen
from traitlets import Bool
from jupyterhub.utils import url_path_join
from cloudharness.auth import AuthClient

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(handler)

class CloudHarnessAuthenticateHandler(BaseHandler):
    """
    Handler for /chkclogin
    Creates a new user based on the keycloak user, and auto starts their server
    """
    def initialize(self, force_new_server, process_user):
        super().initialize()
        self.force_new_server = force_new_server
        self.process_user = process_user

    @gen.coroutine
    def get(self):
        raw_user = yield self.get_current_user()
        if raw_user:
            if self.force_new_server and user.running:
                # Stop user's current server if it is running
                # so we get a new one.
                status = yield raw_user.spawner.poll_and_notify()
                if status is None:
                    yield self.stop_single_user(raw_user)
        else:
            try:
                accessToken = self.request.cookies.get(
                    'kc-access', None) or self.request.cookies.get('accessToken', None)
                print("Token", accessToken)
                if accessToken == '-1' or not accessToken:
                    self.redirect('/hub/logout')

                accessToken = accessToken.value
                user_data = AuthClient.decode_token(accessToken)
                username = user_data['sub']
                print("Username", user_data['preferred_username'])
                raw_user = self.user_from_username(username)

                self.set_login_cookie(raw_user)
            except Exception as e:
                logging.error("Error getting user from session", exc_info=True)
                raise

        user = yield gen.maybe_future(self.process_user(raw_user, self))
        self.redirect(self.get_next_url(user))


class CloudHarnessAuthenticator(Authenticator):
    """
    JupyterHub Authenticator for use with Cloud Harness
    When JupyterHub is configured to use this authenticator, the client 
    needs to set the accessToken domain cookie
    """

    auto_login = True
    login_service = 'chkc'

    force_new_server = Bool(
        True,
        help="""
        Stop the user's server and start a new one when visiting /hub/chlogin
        When set to True, users going to /hub/chlogin will *always* get a
        new single-user server. When set to False, they'll be
        redirected to their current session if one exists.
        """,
        config=True
    )

    def process_user(self, user, handler):
        """
        Do additional arbitrary things to the created user before spawn.
        user is a user object, and handler is a CloudHarnessAuthenticateHandler 
        object. Should return the new user object.
        This method can be a @tornado.gen.coroutine.
        Note: This is primarily for overriding in subclasses
        """
        return user

    def get_handlers(self, app):
        # FIXME: How to do this better?
        extra_settings = {
            'force_new_server': self.force_new_server,
            'process_user': self.process_user
        }
        return [
            ('/chkclogin', CloudHarnessAuthenticateHandler, extra_settings)
        ]

    def login_url(self, base_url):
        return url_path_join(base_url, 'chkclogin')
