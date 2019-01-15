# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import time
from datetime import datetime, timedelta

from wazo_auth import schemas
from xivo.mallow import fields, validate


def get_timestamp_expiration(expires_in):
    token_expiration_date = datetime.now() + timedelta(seconds=expires_in)
    return time.mktime(token_expiration_date.timetuple())


class MicrosoftPostSchema(schemas.BaseSchema):

    scope = fields.List(fields.String(validate=validate.Length(min=1, max=512)))
