import json
from unittest.mock import patch, MagicMock

from aker.testing import FlaskTestCase


__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'


class TestApp(FlaskTestCase):
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
        super().setUp()

        self._patch_sqs()
        self._patch_cloudant()

    def tearDown(self):
        super().tearDown()

        self.sqs_connect_patch.stop()
        self.cloudant_patch.stop()

    def test_index(self):
        self.sqs_queue.count.return_value = 0
        rv = self.app.get('/')
        self.assertEqual(200, rv._status_code)

    def test_status_has_queue_count(self):
        queue_size = 5
        self.sqs_queue.count.return_value = queue_size

        rv = self.app.get('/status')

        self.assertDictEqual(json.loads(rv.data.decode('utf-8')), {'queue_length' : queue_size})

    def test_start_starts_watcher(self):
