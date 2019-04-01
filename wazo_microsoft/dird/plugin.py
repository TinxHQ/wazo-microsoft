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
            'office365',
            self.name,
            unique_column,
            format_columns,
        )
        self._searched_columns = config.get(self.SEARCHED_COLUMNS, [])

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

        contacts = self.office365.get_contacts_with_term(microsoft_token, term, self.endpoint)
        for contact in contacts:
            contact['email'] = services.get_first_email(contact)

            if not contact.get('givenName'):
                contact['givenName'] = ''

        sorted_contacts = sorted(contacts, key=itemgetter('givenName'))

        lowered_term = term.lower()

        def match_fn(entry):
            for column in self._searched_columns:
                column_value = entry.get(column) or ''
                if lowered_term in str(column_value).lower():
                    return True
            return False

        return [self._source_result_from_content(content) for content in sorted_contacts if match_fn(content)]

    def first_match(self, term, args=None):
        return None

    def _source_result_from_content(self, content):
        return self._SourceResult(content)
