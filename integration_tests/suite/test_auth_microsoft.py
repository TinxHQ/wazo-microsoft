# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import requests
from hamcrest import (
    assert_that,
    empty,
    calling,
    has_entries,
    has_key,
    has_properties,
    has_property,
    none,
    not_,
)

from xivo_test_helpers import until
from xivo_test_helpers.hamcrest.raises import raises

from .helpers.base import BaseTestCase


MICROSOFT = 'microsoft'
AUTHORIZE_URL = 'http://localhost:{}/microsoft/authorize/a-state'


class TestAuthMicrosoft(BaseTestCase):

    asset = 'auth_microsoft'

    def test_when_create_authorize_get_then_does_not_raise(self):
        self.client.external.create(MICROSOFT, self.admin_user_uuid, {})

        self._simulate_user_authentication()

        assert_that(
            calling(self.client.external.get).with_args(MICROSOFT, self.admin_user_uuid),
            not_(raises(requests.HTTPError))
        )

    def test_when_create_then_url_returned(self):
        response = self.client.external.create(MICROSOFT, self.admin_user_uuid, {})

        assert_that(response, has_key('authorization_url'))

    def test_when_create_twice_without_authorize_then_not_created(self):
        self.client.external.create(MICROSOFT, self.admin_user_uuid, {})

        assert_that(
            calling(self.client.external.create).with_args(MICROSOFT, self.admin_user_uuid, {}),
            not_(raises(requests.HTTPError))
        )

    def test_when_create_twice_with_authorize_then_does_not_raise(self):
        self.client.external.create(MICROSOFT, self.admin_user_uuid, {})
        self._simulate_user_authentication()
        self.client.external.create(MICROSOFT, self.admin_user_uuid, {})
        self._simulate_user_authentication()

        assert_that(
            calling(self.client.external.get).with_args(MICROSOFT, self.admin_user_uuid),
            not_(raises(requests.HTTPError))
        )

    def test_when_delete_then_not_found(self):
        _assert_that_raises_http_error(404, self.client.external.delete, MICROSOFT, self.admin_user_uuid)

    def test_when_delete_nothing_then_not_found(self):
        _assert_that_raises_http_error(404, self.client.external.delete, MICROSOFT, self.admin_user_uuid)

    def test_when_get_then_token_returned(self):
        self.client.external.create(MICROSOFT, self.admin_user_uuid, {})
        self._simulate_user_authentication()

        response = self.client.external.get(MICROSOFT, self.admin_user_uuid)

        assert_that(response, has_entries(
            access_token=not_(none()),
            token_expiration=not_(none()),
            scope=not_(empty()),
        ))

    def test_given_no_external_auth_when_delete_then_not_found(self):
        _assert_that_raises_http_error(404, self.client.external.delete, MICROSOFT, self.admin_user_uuid)

    def test_given_no_external_auth_when_get_then_not_found(self):
        _assert_that_raises_http_error(404, self.client.external.get, MICROSOFT, self.admin_user_uuid)

    def test_given_no_external_auth_confirmed_when_get_then_not_found(self):
        self.client.external.create(MICROSOFT, self.admin_user_uuid, {})

        _assert_that_raises_http_error(404, self.client.external.get, MICROSOFT, self.admin_user_uuid)
        self._simulate_user_authentication()
        self.client.external.get(MICROSOFT, self.admin_user_uuid)

    def _simulate_user_authentication(self):
        authorize_url = AUTHORIZE_URL.format(self.service_port(80, 'oauth2sync'))
        response = requests.get(authorize_url)
        response.raise_for_status()

        def _is_microsoft_token_fetched():
            try:
                return self.client.external.get(MICROSOFT, self.admin_user_uuid)
            except requests.HTTPError:
                return False

        response = until.true(_is_microsoft_token_fetched, timeout=20, interval=1)


def _assert_that_raises_http_error(status_code, fn, *args, **kwargs):
    assert_that(
        calling(fn).with_args(*args, **kwargs),
        raises(requests.HTTPError).matching(
            has_property('response', has_properties('status_code', status_code))
        )
    )
