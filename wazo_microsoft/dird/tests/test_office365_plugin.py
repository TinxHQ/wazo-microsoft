# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from unittest import TestCase

from hamcrest import assert_that, calling, not_, raises

from ..plugin import Office365Plugin


class TestOffice365Plugin(TestCase):

    DEPENDENCIES = {
        'config': {
            'auth': {
                'host': '9497',
            },
            'endpoint': 'www.bros.com',
            'name': 'office365',
            'user_agent': 'luigi',
            'format_columns': {
                'display_name': "{firstname} {lastname}",
                'name': "{firstname} {lastname}",
                'reverse': "{firstname} {lastname}",
                'phone_mobile': "{mobile}",
            },
        },
    }

    def setUp(self):
        self.source = Office365Plugin()

    def test_load(self):
        assert_that(
            calling(self.source.load).with_args(self.DEPENDENCIES),
            not_(raises(Exception))
        )
