import unittest
from unittest.mock import patch, MagicMock

from application import app


__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'


class FlaskTestCase(unittest.TestCase):

    def _patch_sqs(self):
        self.sqs_connect_patch = patch('boto.sqs.connect_to_region')
        self.sqs_connect = self.sqs_connect_patch.start()
        self.sqs_connection = MagicMock()
        self.sqs_queue = MagicMock()
        self.sqs_connection.get_queue.return_value = self.sqs_queue
        self.sqs_connection.create_queue.return_value = self.sqs_queue
        self.sqs_connect.return_value = self.sqs_connection

    def _patch_cloudant(self):
        self.cloudant_patch = patch('cloudant.Account')
        self.cloudant_account_factory = self.cloudant_patch.start()
        self.cloudant_account = self.cloudant_account_factory.return_value

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

        self._patch_sqs()
        self._patch_cloudant()

    def tearDown(self):
        self.sqs_connect_patch.stop()
        self.cloudant_patch.stop()

    def test_index(self):
        self.sqs_queue.count.return_value = 1
        rv = self.app.get('/')
        print(rv.data.decode('utf-8'))
        self.assertEqual(200, rv._status_code)

if __name__ == '__main__':
    unittest.main()
