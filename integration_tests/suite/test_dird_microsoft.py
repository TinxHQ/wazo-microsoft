# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import requests
import unittest

from hamcrest import (
    assert_that,
    calling,
    contains,
    empty,
    has_entries,
    has_entry,
    has_item,
    has_properties,
    has_property,
    is_,
    not_,
)
from wazo_dird_client import Client as DirdClient
from xivo_test_helpers.auth import AuthClient as AuthMock
from xivo_test_helpers.hamcrest.raises import raises

from .helpers.base_dird import (BaseOffice365PluginTestCase,
                                BaseOffice365TestCase)

requests.packages.urllib3.disable_warnings()
VALID_TOKEN_MAIN_TENANT = 'valid-token-master-tenant'
MAIN_TENANT = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee10'


class TestOffice365Plugin(BaseOffice365PluginTestCase):

    asset = 'plugin_dird_microsoft'

    def config(self):
        return {
            'auth': {
                'host': 'localhost',
                'port': self.service_port(9497, 'auth-mock'),
                'verify_certificate': False,
            },
            'endpoint': 'http://localhost:{}/me/contacts'.format(self.service_port(80, 'microsoft-mock')),
            'first_matched_columns': [],
            'format_columns': {
                'number': '{businessPhones[0]}',
                'email': '{emailAddresses[0][address]}',
            },
            'name': 'office365',
            'searched_columns': [],
            'type': 'office365',
        }

    def test_plugin_lookup(self):
        self.auth_mock.set_external_auth(self.MICROSOFT_EXTERNAL_AUTH)

        result = self.backend.search('war', self.LOOKUP_ARGS)

        assert_that(result, contains(has_entries(
            number='5555555555',
            email='wbros@wazoquebec.onmicrosoft.com',
            **self.WARIO
        )))


class TestOffice365PluginWrongEndpoint(BaseOffice365PluginTestCase):

    asset = 'plugin_dird_microsoft'

    def config(self):
        return {
            'auth': {
                'host': 'localhost',
                'port': self.service_port(9497, 'auth-mock'),
                'verify_certificate': False,
            },
            'endpoint': 'wrong-endpoint',
            'first_matched_columns': [],
            'format_columns': {
                'display_name': "{firstname} {lastname}",
                'name': "{firstname} {lastname}",
                'reverse': "{firstname} {lastname}",
                'phone_mobile': "{mobile}",
            },
            'name': 'office365',
            'searched_columns': [],
            'type': 'office365',
        }

    def test_plugin_lookup_with_wrong_endpoint(self):
        self.auth_mock.set_external_auth(self.MICROSOFT_EXTERNAL_AUTH)

        result = self.backend.search('war', self.LOOKUP_ARGS)

        assert_that(result, is_(empty()))


class TestDirdClientOffice365Plugin(BaseOffice365TestCase):

    asset = 'dird_microsoft'
    BACKEND = 'office365'

    def config(self):
        return {
            'auth': {
                'host': 'auth-mock',
                'port': 9497,
                'verify_certificate': False,
            },
            'endpoint': 'http://microsoft-mock:80/me/contacts',
            'first_matched_columns': [],
            'format_columns': {
                'display_name': "{displayName}",
                'name': "{displayName}",
                'reverse': "{displayName}",
                'phone_mobile': "{mobilePhone}",
            },
            'name': 'office365',
            'searched_columns': [],
            'type': 'office365',
        }

    def setUp(self):
        super().setUp()
        port = self.service_port(9489, 'dird')
        dird_config = {
            'host': 'localhost',
            'port': port,
            'token': VALID_TOKEN_MAIN_TENANT,
            'verify_certificate': False,
        }
        self.client = DirdClient(**dird_config)

    def tearDown(self):
        try:
            response = self.client.backends.list_sources(backend=self.BACKEND)
            sources = response['items']
            for source in sources:
                self.client.backends.delete_source(backend=self.BACKEND, source_uuid=source['uuid'])
        except requests.HTTPError:
            pass

    def test_when_create_source_then_no_error(self):
        assert_that(
            calling(self.client.backends.create_source).with_args(
                backend=self.BACKEND,
                body=self.config(),
            ),
            not_(raises(requests.HTTPError))
        )

    def test_given_source_when_delete_then_ok(self):
        source = self.client.backends.create_source(backend=self.BACKEND, body=self.config())

        assert_that(
            calling(self.client.backends.delete_source).with_args(
                backend=self.BACKEND,
                source_uuid=source['uuid'],
            ),
            not_(raises(requests.HTTPError))
        )

    def test_when_delete_then_raises(self):
        assert_that(
            calling(self.client.backends.delete_source).with_args(
                backend=self.BACKEND,
                source_uuid='a-non-existing-source-uuid',
            ),
            raises(requests.HTTPError).matching(
                has_property('response', has_properties('status_code', 404))
            )
        )

    def test_given_source_when_get_then_ok(self):
        source = self.client.backends.create_source(backend=self.BACKEND, body=self.config())

        assert_that(
            calling(self.client.backends.get_source).with_args(
                backend=self.BACKEND,
                source_uuid=source['uuid'],
            ),
            not_(raises(requests.HTTPError))
        )

    def test_given_source_when_edit_then_ok(self):
        source = self.client.backends.create_source(backend=self.BACKEND, body=self.config())
        source.update({'name': 'a-new-name'})

        assert_that(
            calling(self.client.backends.edit_source).with_args(
                backend=self.BACKEND,
                source_uuid=source['uuid'],
                body=source,
            ),
            not_(raises(requests.HTTPError))
        )

    def test_given_source_when_list_sources_then_ok(self):
        source = self.client.backends.create_source(backend=self.BACKEND, body=self.config())

        sources = self.client.backends.list_sources(backend=self.BACKEND)

        assert_that(next(iter(sources['items'])), has_entry('uuid', source['uuid']))

    def test_given_source_when_list_then_ok(self):
        self.client.backends.create_source(backend=self.BACKEND, body=self.config())

        backends = self.client.backends.list()

        assert_that(backends['items'], has_item({'name': self.BACKEND}))


@unittest.skip('cannot do the setup with the REST API')
class TestDirdOffice365Plugin(BaseOffice365TestCase):

    asset = 'dird_microsoft'

    BACKEND = 'office365'
    display_body = {
        'name': 'default',
        'columns': [
            {'title': 'Firstname', 'field': 'firstname'},
            {'title': 'Lastname', 'field': 'lastname'},
            {'title': 'Number', 'field': 'number'},
        ],
    }

    def config(self):
        return {
            'auth': {
                'host': 'auth-mock',
                'port': 9497,
                'verify_certificate': False,
            },
            'endpoint': 'http://microsoft-mock:80/me/contacts',
            'first_matched_columns': [],
            'format_columns': {
                'firstname': "{givenName}",
                'lastname': "{surname}",
                'number': "{businessPhones[0]}",
            },
            'name': 'office365',
            'searched_columns': [],
            'type': 'office365',
        }

    def setUp(self):
        super().setUp()
        port = self.service_port(9489, 'dird')
        dird_config = {
            'host': 'localhost',
            'port': port,
            'token': VALID_TOKEN_MAIN_TENANT,
            'verify_certificate': False,
        }
        self.client = DirdClient(**dird_config)
        self.display = self.client.display.create(**self.display_body)
        self.source = self.client.backends.create_source(
            backend=self.BACKEND,
            body=self.config(),
            tenant_uuid=MAIN_TENANT
        )
        profile_body = {
            'name': 'default',
            'display': self.display,
            'services': {'lookup': {'sources': [self.source]}},
        }
        self.profile = self.client.profile.create(**profile_body)
        self.auth_client_mock = AuthMock(host='0.0.0.0', port=self.service_port(9497, 'auth-mock'))

    def tearDown(self):
        try:
            self.client.backends.delete_source(
                backend=self.BACKEND,
                source_uuid=self.source['uuid'],
            )
            self.auth_client_mock.reset_external_auth()
        except requests.HTTPError:
            pass

        try:
            self.client.display.delete(self.display['uuid'])
        except requests.HTTPError:
            pass

        try:
            self.client.profile.delete(self.profile['uuid'])
        except requests.HTTPError:
            pass

    def test_given_microsoft_when_lookup_then_contacts_fetched(self):
        self.auth_client_mock.set_external_auth(self.MICROSOFT_EXTERNAL_AUTH)

        result = self.client.directories.lookup(term='war', profile='default', token='valid-token')
        result = result['results'][0]['column_values']

        assert_that(result, has_item('Wario Bros'))

    def test_given_no_microsoft_when_lookup_then_no_result(self):
        result = self.client.directories.lookup(term='war', profile='default', token='valid-token')
        result = result['results']

        assert_that(result, is_(empty()))


@unittest.skip('cannot do the setup with the REST API')
class TestDirdOffice365PluginNoEndpoint(BaseOffice365TestCase):

    asset = 'dird_microsoft'

    BACKEND = 'office365'

    def config(self):
        return {
            'auth': {
                'host': 'auth-mock',
                'port': 9497,
                'verify_certificate': False,
            },
            'first_matched_columns': [],
            'format_columns': {
                'firstname': "{givenName}",
                'lastname': "{surname}",
                'reverse': "{displayName}",
                'phone_mobile': "{mobilePhone}",
            },
            'name': 'office365',
            'searched_columns': [],
            'type': 'office365',
        }

    def setUp(self):
        super().setUp()
        port = self.service_port(9489, 'dird')
        dird_config = {
            'host': 'localhost',
            'port': port,
            'token': VALID_TOKEN_MAIN_TENANT,
            'verify_certificate': False,
        }
        self.client = DirdClient(**dird_config)
        self.source = self.client.backends.create_source(
            backend=self.BACKEND,
            body=self.config(),
            tenant_uuid=MAIN_TENANT
        )
        self.auth_client_mock = AuthMock(host='0.0.0.0', port=self.service_port(9497, 'auth-mock'))

    def tearDown(self):
        try:
            self.client.backends.delete_source(
                backend=self.BACKEND,
                source_uuid=self.source['uuid'],
            )
            self.auth_client_mock.reset_external_auth()
        except requests.HTTPError:
            pass

    def test_given_microsoft_when_lookup_with_no_endpoint_then_no_error(self):
        self.auth_client_mock.set_external_auth(self.MICROSOFT_EXTERNAL_AUTH)

        assert_that(
            calling(self.client.directories.lookup).with_args(
                term='war',
                profile='default',
                token='valid-token',
            ),
            not_(raises(Exception))
        )
