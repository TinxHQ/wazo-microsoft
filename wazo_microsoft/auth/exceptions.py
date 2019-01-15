# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from xivo.rest_api_helpers import APIException


class ExternalAuthNotAuthorizedYetException(APIException):

    def __init__(self, auth_type):
        msg = 'This external authentification method has been set but not authorized: "{}"'.format(auth_type)
        details = {'type': auth_type}
        super().__init__(401, msg, 'Unauthorized', details, auth_type)
