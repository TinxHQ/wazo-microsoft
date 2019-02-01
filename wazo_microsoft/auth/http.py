# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import os
import time
from datetime import datetime
from threading import Thread

from flask import request
from requests_oauthlib import OAuth2Session
from wazo_auth import http
from wazo_auth.exceptions import UserParamException

from .helpers import MicrosoftPostSchema, get_timestamp_expiration
from .websocket_oauth2 import WebSocketOAuth2

logger = logging.getLogger(__name__)

# Allow token scope to not match requested scope. (Requests-OAuthlib raises exception on scope mismatch by default.)
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_IGNORE_SCOPE_CHANGE'] = '1'


class MicrosoftAuth(http.AuthResource):

    auth_type = 'microsoft'

    def __init__(self, external_auth_service, config):
        self.authorization_base_url = config[self.auth_type]['authorization_base_url']
        self.client_id = config[self.auth_type]['client_id']
        self.client_secret = config[self.auth_type]['client_secret']
        self.external_auth_service = external_auth_service
        self.redirect_uri = config[self.auth_type]['redirect_uri']
        self.scope = config[self.auth_type]['scope']
        self.token_url = config[self.auth_type]['token_url']
        self.oauth2 = OAuth2Session(self.client_id, scope=self.scope, redirect_uri=self.redirect_uri)
        self.websocket = WebSocketOAuth2(
            host=config[self.auth_type]['websocket_host'],
            auth=self.oauth2,
            external_auth=self.external_auth_service,
            client_secret=self.client_secret,
            token_url=self.token_url,
            auth_type=self.auth_type
        )

    @http.required_acl('auth.users.{user_uuid}.external.microsoft.create')
    def post(self, user_uuid):
        args, errors = MicrosoftPostSchema().load(request.get_json())

        if errors:
            raise UserParamException.from_errors(errors)

        if args.get('scope'):
            self.oauth2.scope = args.get('scope')

        logger.debug('User(%s) is creating an authorize url for Microsoft', str(user_uuid))

        authorization_url, state = self.oauth2.authorization_url(self.authorization_base_url)
        logger.debug('Authorization url : {}'.format(authorization_url))

        websocket_thread = Thread(target=self.websocket.run, args=(state, user_uuid), name='websocket_thread')
        websocket_thread.daemon = True
        websocket_thread.start()

        return {'authorization_url': authorization_url}, 201

    @http.required_acl('auth.users.{user_uuid}.external.microsoft.read')
    def get(self, user_uuid):
        data = self.external_auth_service.get(user_uuid, self.auth_type)

        expiration = data.get('token_expiration')

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
        return time.mktime(datetime.now().timetuple()) + 30 > token_expiration

    def _refresh_token(self, user_uuid, data):
        oauth2 = OAuth2Session(self.client_id, token=data)
        token_data = oauth2.refresh_token(self.token_url, client_id=self.client_id, client_secret=self.client_secret)

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