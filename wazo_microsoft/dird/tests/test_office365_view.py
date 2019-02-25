# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from unittest import TestCase
from mock import Mock, ANY

from ..http import MicrosoftList, MicrosoftItem
from ..view import Office365View


class TestOffice365View(TestCase):

    def setUp(self):
        self.plugin = Office365View()
        self.api = Mock()

    def test_when_load_then_routes_added(self):
        dependencies = {
            'config': {
                'auth': Mock()
            },
            'http_namespace': Mock(),
            'api': self.api,
            'services': {
                'source': Mock()
            },
        }

        self.plugin.load(dependencies)

        self.api.add_resource.assert_any_call(
            MicrosoftList, ANY, resource_class_args=ANY,
        )
        self.api.add_resource.assert_any_call(
            MicrosoftItem, ANY, resource_class_args=ANY,
        )
