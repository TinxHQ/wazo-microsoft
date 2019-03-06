# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from operator import itemgetter

from wazo_dird import BaseSourcePlugin, make_result_class

from .exceptions import MicrosoftTokenNotFoundException
from . import services

logger = logging.getLogger(__name__)


class Office365Plugin(BaseSourcePlugin):

    def load(self, dependencies):
        config = dependencies['config']
        self.auth = config['auth']
        self.name = config['name']
        self.endpoint = config['endpoint']
        self.office365 = services.Office365Service()

        unique_column = 'id'
        format_columns = dependencies['config'].get(self.FORMAT_COLUMNS, {})

        self._SourceResult = make_result_class(
            self.name,
            unique_column,
            format_columns,
        )

    def search(self, term, args=None):
        logger.debug('Searching term=%s', term)

        if not args:
            logger.debug('No args provided')
            return []

        user_uuid = args.get('xivo_user_uuid')
        token = args.get('token')

        if not token:
            logger.debug('Unable to search through Office365 without a token.')
            return []

        try:
            microsoft_token = services.get_microsoft_access_token(user_uuid, token, **self.auth)
        except MicrosoftTokenNotFoundException:
            return []

        contacts_output = self.office365.get_contacts_with_term(microsoft_token, term, self.endpoint)

        contacts = []
        for person in contacts_output:
            email = services.get_first_email(person)
            phone = services.get_first_phone(person)
            contacts.append({
                'id': person.get('id', '') or '',
                'firstname': person.get('givenName', '') or '',
                'lastname': person.get('surname', '') or '',
                'job': person.get('pofession', '') or '',
                'mobile': person.get('mobilePhone', '') or '',
                'phone': phone,
                'email': email if '@' in email else '',
                'entity': '',
                'fax': '',
            })

        contacts = sorted(contacts, key=itemgetter('firstname'))

        return [self._source_result_from_content(content) for content in contacts]

    def first_match(self, term, args=None):
        return None

    def _source_result_from_content(self, content):
        return self._SourceResult(content)
