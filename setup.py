#!/usr/bin/env python3
# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from setuptools import find_packages
from setuptools import setup

setup(
    name='wazo_microsoft',
    version='2.0.2',
    description='Wazo Microsoft authentication connector',

    author='Wazo Authors',
    author_email='dev@wazo.io',

    url='http://wazo.io',

    packages=find_packages(),
    include_package_data=True,
    package_data={
        'wazo_microsoft': ['*/api.yml'],
    },
    entry_points={
        'wazo_auth.external_auth': [
            'microsoft = wazo_microsoft.auth.plugin:MicrosoftPlugin',
        ],
        'wazo_dird.backends': [
            'office365 = wazo_microsoft.dird.plugin:Office365Plugin',
        ],
        'wazo_dird.views': [
            'office365_view = wazo_microsoft.dird.view:Office365View'
        ]
    }
)
