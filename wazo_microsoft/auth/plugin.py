# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import logging
import os
import time
from datetime import datetime, timedelta
from threading import Thread

import websocket
from flask import request
from requests_oauthlib import OAuth2Session
from wazo_auth import exceptions as wazo_auth_exceptions
from wazo_auth import http, schemas
from xivo.mallow import fields, validate

from . import exceptions

logger = logging.getLogger(__name__)

# Allow token scope to not match requested scope. (Requests-OAuthlib raises exception on scope mismatch by default.)
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_IGNORE_SCOPE_CHANGE'] = '1'


class MicrosoftPostSchema(schemas.BaseSchema):

    scope = fields.List(fields.String(validate=validate.Length(min=1, max=512)))


class MicrosoftAuth(http.AuthResource):

    auth_type = 'microsoft'
    token_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/token'
    authorization_base_url = 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize'
    refresh_url = token_url
    redirect_uri = 'https://oauth.wazo.io/microsoft/authorize'
    scope = [
        'offline_access',
        'Contacts.Read'
    ]

    def __init__(self, external_auth_service, config):
        self.external_auth_service = external_auth_service
        self.client_id = config['microsoft']['client_id']
        self.client_secret = config['microsoft']['client_secret']
        self.oauth2 = OAuth2Session(self.client_id, scope=self.scope, redirect_uri=self.redirect_uri)
        self.websocket = WebSocketOAuth2(
            self.oauth2,
            self.external_auth_service,
            self.client_secret,
            self.token_url,
            self.auth_type
        )

    @http.required_acl('auth.users.{user_uuid}.external.microsoft.create')
    def post(self, user_uuid):
        args, errors = MicrosoftPostSchema().load(request.get_json())

        if errors:
            raise wazo_auth_exceptions.UserParamException.from_errors(errors)

        if args.get('scope'):
            self.oauth2.scope = args.get('scope')

        logger.debug('User(%s) is creating an authorize url for Microsoft', str(user_uuid))
        data = {
            'client_id': self.client_id,
            'scope': args.get('scope', self.scope)
        }
        self.external_auth_service.create(user_uuid, self.auth_type, data)
        authorization_url, state = self.oauth2.authorization_url(self.authorization_base_url)
        logger.debug('Authorization url : {}'.format(authorization_url))

        websocket_thread = Thread(target=self.websocket.run, args=(state, user_uuid), name='websocket_thread')
        websocket_thread.start()

        return {'authorization_url': authorization_url}, 201

    @http.required_acl('auth.users.{user_uuid}.external.microsoft.read')
    def get(self, user_uuid):
        data = self.external_auth_service.get(user_uuid, self.auth_type)

        token = data.get('access_token')
        expiration = data.get('token_expiration')

        if not token:
            raise exceptions.ExternalAuthNotAuthorizedYetException(self.auth_type)

        if self._is_token_expired(expiration):
            return self._refresh_token(user_uuid, data)

        return self._create_get_response(data)

    @http.required_acl('auth.users.{user_uuid}.external.microsoft.delete')
    def delete(self, user_uuid):
        self.external_auth_service.delete(user_uuid, self.auth_type)
        return '', 204

    def _is_token_expired(self, token_expiration):
        if token_expiration is None:
            return True
        return time.mktime(datetime.now().timetuple()) > token_expiration

    def _refresh_token(self, user_uuid, data):
        oauth2 = OAuth2Session(self.client_id, token=data)
        token_data = oauth2.refresh_token(self.refresh_url, client_id=self.client_id, client_secret=self.client_secret)

        logger.debug('refresh token info: %s', token_data)
        data['access_token'] = token_data['access_token']
        data['token_expiration'] = get_timestamp_expiration(token_data['expires_in'])

        self.external_auth_service.update(user_uuid, self.auth_type, data)

        return self._create_get_response(data)

    @staticmethod
    def _create_get_response(data):
        return {
            'access_token': data['access_token'],
            'expiration': data['token_expiration'],
            'scope': data.get('scope'),
        }, 200


class WebSocketOAuth2(Thread):

    def __init__(self, auth, external_auth, client_secret, token_url, auth_type):
        Thread.__init__(self)

        self.host = 'wss://oauth.wazo.io'
        self.oauth2 = auth
        self.external_auth_service = external_auth
        self.client_secret = client_secret
        self.token_url = token_url
        self.user_uuid = None
        self.auth_type = auth_type

    def run(self, state, user_uuid):
        self.user_uuid = user_uuid

        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(
            '{}/ws/{}'.format(self.host, state),
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close)
        ws.run_forever()

    def _on_message(self, ws, message):
        logger.debug("Confirmation has been received on websocketOAuth.")
        msg = json.loads(message)
        ws.close()
        self.create_first_token(self.user_uuid, msg.get('code'))

    def _on_error(self, ws, error):
        logger.error(error)

    def _on_close(self, ws):
        logger.debug("WebsocketOAuth closed.")

    def create_first_token(self, user_uuid, code):
        token_data = self.oauth2.fetch_token(self.token_url, client_secret=self.client_secret, code=code)

        data = {
            'access_token': token_data['access_token'],
            'refresh_token': token_data['refresh_token'],
            'token_expiration': get_timestamp_expiration(token_data['expires_in'])
        }
        self.external_auth_service.update(user_uuid, self.auth_type, data)


def get_timestamp_expiration(expires_in):
    token_expiration_date = datetime.now() + timedelta(seconds=expires_in)
    return time.mktime(token_expiration_date.timetuple())


class Plugin:

    def load(self, dependencies):
        api = dependencies['api']
        args = (dependencies['external_auth_service'], dependencies['config'])

        api.add_resource(
            MicrosoftAuth,
            '/users/<uuid:user_uuid>/external/microsoft',
            resource_class_args=args
        )
