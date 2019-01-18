# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from .microsoft_auth import MicrosoftAuth


class Plugin:

    def load(self, dependencies):
        api = dependencies['api']
        args = (dependencies['external_auth_service'], dependencies['config'])

        api.add_resource(
            MicrosoftAuth,
            '/users/<uuid:user_uuid>/external/microsoft',
            resource_class_args=args
        )
