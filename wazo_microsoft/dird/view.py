# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from wazo_dird.helpers import BaseBackendView

from .http import MicrosoftItem, MicrosoftList, MicrosoftContactList


logger = logging.getLogger(__name__)


class Office365View(BaseBackendView):

    backend = 'office365'
    item_resource = MicrosoftItem
    list_resource = MicrosoftList
    contact_list_resource = MicrosoftContactList

    def load(self, dependencies):
        super().load(dependencies)
        api = dependencies['api']
        config = dependencies['config']
        auth_config = config['auth']
        source_service = dependencies['services']['source']
        args = (auth_config, config, source_service)

        api.add_resource(
            self.contact_list_resource,
            "/backends/office365/sources/<source_uuid>/contacts",
            resource_class_args=args,
        )
