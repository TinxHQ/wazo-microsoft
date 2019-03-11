# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from wazo_dird.helpers import BaseBackendView

from .http import MicrosoftItem, MicrosoftList


class Office365View(BaseBackendView):

    backend = 'office365'
    item_resource = MicrosoftItem
    list_resource = MicrosoftList
