import base64
import io
import json
import os
import urllib
import urllib.request

import jose.jwt
from jupyterhub.auth import Authenticator
from jupyterhub.handlers import BaseHandler
from tornado import gen
from tornado.httpclient import HTTPRequest, AsyncHTTPClient, HTTPClient
from traitlets import Unicode, Dict, Set, observe

import requests

import uuid

from traitlets import Bool
from tornado import gen

from jupyterhub.auth import Authenticator
from jupyterhub.handlers import BaseHandler
from jupyterhub.utils import url_path_join

from .utils import get_keycloak_data

class CloudHarnessAuthenticateHandler(BaseHandler):
    """
    Handler for /chkclogin
    Creates a new user with a random UUID, and auto starts their server
    """
    def initialize(self, force_new_server, process_user):
        super().initialize()
        self.force_new_server = force_new_server
        self.process_user = process_user

    @gen.coroutine
    def get(self):
        print('*'*40)
        print('QUERY: ')
        print(self.request.query)
        print('*'*40)
        print('COOKIES: ')
        print(self.request.cookies)
        print('*'*40)
        raw_user = yield self.get_current_user()
        if raw_user:
            if self.force_new_server and user.running:
                # Stop user's current server if it is running
                # so we get a new one.
                status = yield raw_user.spawner.poll_and_notify()
                if status is None:
                    yield self.stop_single_user(raw_user)
        else:
            accessToken = self.request.cookies.get('accessToken', None)
            print('*'*40)
            print(f'accessToken: {accessToken}')
            print('*'*40)

            if accessToken:
                accessToken = accessToken.value
            print('*'*40)
            print(f'Token: {accessToken}')
            print('*'*40)
            keycloak_id, keycloak_data = get_keycloak_data(accessToken)
            username = keycloak_id
            print('*'*40)
            print(f'Username: {username}')
            print('*'*40)
            # username = str(uuid.uuid4())
            raw_user = self.user_from_username(username)
            self.set_login_cookie(raw_user)
        user = yield gen.maybe_future(self.process_user(raw_user, self))
        self.redirect(self.get_next_url(user))


class CloudHarnessAuthenticator(Authenticator):
    """
    JupyterHub Authenticator for use with tmpnb.org
    When JupyterHub is configured to use this authenticator, visiting the home
    page immediately logs the user in with a randomly generated UUID if they
    are already not logged in, and spawns a server for them.
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
        user is a user object, and handler is a TmpAuthenticateHandler object
        Should return the new user object.
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