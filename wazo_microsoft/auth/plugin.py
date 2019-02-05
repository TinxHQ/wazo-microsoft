# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from .http import MicrosoftAuth


logger = logging.getLogger(__name__)


class Plugin:

    def load(self, dependencies):
        api = dependencies['api']
        config = dependencies['config']
        args = (dependencies['external_auth_service'], config)

        if not config['microsoft']['client_id'] or not config['microsoft']['client_secret']:
            logger.warning("Plugin unable to load, microsoft 'client_id' or 'client_secret' missing.")
            return

        api.add_resource(
            MicrosoftAuth,
            '/users/<uuid:user_uuid>/external/microsoft',
            resource_class_args=args
        )
