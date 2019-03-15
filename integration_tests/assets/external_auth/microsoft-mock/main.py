# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from flask import Flask, request
from flask_restful import Resource, Api


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MicrosoftMock(Resource):

    def get(self):
        term = request.args.get('term')
        logger.debug('Looking for term: {}.'.format(term))
        data = {
            "@odata.context": "a-odata-context",
            "value": [
                {
                    "@odata.etag": "W/\"an-odata-etag\"",
                    "id": "an-id",
                    "displayName": "Wario Bros",
                    "givenName": "Wario",
                    "surname": "Bros",
                    "mobilePhone": "",
                    "businessPhones": ['5555555555'],
                    "emailAddresses": [
                        {
                            "address": "wbros@wazoquebec.onmicrosoft.com"
                        },
                        {},
                        {}
                    ]
                }
            ]
        }
        return data, 200


class MicrosoftErrorMock(Resource):

    def get(self):
        logger.debug('Microsoft is sending an error response.')
        return '', 404


if __name__ == '__main__':
    app = Flask('microsoft')
    api = Api(app)
    api.add_resource(MicrosoftMock, '/me/contacts')
    api.add_resource(MicrosoftErrorMock, '/me/contacts/error')
    app.run(debug=True, host='0.0.0.0', port=80)
