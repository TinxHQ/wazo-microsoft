# Copyright 2015-2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+
import os
import logging

from stevedore import DriverManager
from mock import Mock
from xivo_test_helpers.asset_launching_test_case import AssetLaunchingTestCase
from xivo_test_helpers.auth import AuthClient as AuthMock


logger = logging.getLogger(__name__)

ASSET_ROOT = os.path.join(os.path.dirname(__file__), '../..', 'assets')


class BackendWrapper:

    def __init__(self, backend, dependencies):
        manager = DriverManager(
            namespace='wazo_dird.backends',
            name=backend,
            invoke_on_load=True,
        )
        self._source = manager.driver
        self._source.load(dependencies)

    def unload(self):
        self._source.unload()

    def search(self, term, profile):
        return [r.fields for r in self.search_raw(term, profile)]

    def search_raw(self, term, profile):
        return self._source.search(term, profile)

    def first(self, term):
        return self._source.first_match(term).fields

    def list(self, source_ids):
        results = self._source.list(source_ids)
        return [r.fields for r in results]


class BaseOffice365TestCase(AssetLaunchingTestCase):

    assets_root = ASSET_ROOT
    service = 'dird'

    MICROSOFT_EXTERNAL_AUTH = {
        "access_token": "an-access-token",
        "scope": "a-scope",
        "token_expiration": 42
    }

    LOOKUP_ARGS = {
        'xivo_user_uuid': 'a-xivo-uuid',
        'token': 'a-token',
    }

    WARIO = {
        'givenName': 'Wario',
        'surname': 'Bros',
        'mobilePhone': '',
    }


class BaseOffice365PluginTestCase(BaseOffice365TestCase):

    asset = 'plugin_dird_microsoft'

    def setUp(self):
        super().setUp()
        self.auth_mock = AuthMock(host='0.0.0.0', port=self.service_port(9497, 'auth-mock'))
        self.backend = BackendWrapper(
            'office365',
            {
                'config': self.config(),
                'api': Mock()
            }
        )

    def tearDown(self):
        self.backend.unload()
        self.auth_mock.reset_external_auth()
