import json
from unittest.mock import patch, MagicMock

import aker
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

        # For get('_db_updates')
        response = MagicMock()
        response.iter_lines.return_value = [b'line1', b'line2']
        self.cloudant_account.get.return_value = response

    def _patch_dynamodb(self):
        self.dynamo_table_mock = patch('boto.dynamodb2.table.Table')
        self.dynamo_table_factory = self.dynamo_table_mock.start()

        self.dynamo_table = self.dynamo_table_factory.return_value

        # Happy path: table exists
        self.last_seq = {'worker': 'aker', 'last_seq': '123'}
        self.dynamo_table.get_item.return_value = self.last_seq

    def setUp(self):
        super().setUp()

        self._patch_sqs()
        self._patch_cloudant()
        self._patch_dynamodb()

    def tearDown(self):
        super().tearDown()

        self.sqs_connect_patch.stop()
        self.cloudant_patch.stop()
        self.dynamo_table_mock.stop()

    def test_index(self):
        rv = self.app.get('/')
        self.assertEqual(200, rv._status_code)

    def test_status_has_queue_count(self):
        queue_size = 5
        self.sqs_queue.count.return_value = queue_size

        rv = self.app.get('/status')

        self.assertEqual(json.loads(rv.data.decode('utf-8'))['queue_length'], queue_size)

    def test_status_has_version(self):
        queue_size = 5
        self.sqs_queue.count.return_value = queue_size

        rv = self.app.get('/status')

        self.assertEqual(json.loads(rv.data.decode('utf-8'))['version'], aker.__version__)

    def test_status_has_running(self):
        queue_size = 5
        self.sqs_queue.count.return_value = queue_size

        rv = self.app.get('/status')

        self.assertTrue('running' in json.loads(rv.data.decode('utf-8')))

    def test_returns_500_if_watcher_not_running(self):
        import application

        # warm up
        self.app.get('/')

        application._updates.stop(1)
        self.assertFalse(application._updates.running)

        rv = self.app.get('/')
        self.assertEqual(500, rv._status_code)

    def test_status_has_last_seq(self):
        self.sqs_queue.count.return_value = 0

        rv = self.app.get('/status')

        self.assertEqual(json.loads(rv.data.decode('utf-8'))['last_seq'], self.last_seq['last_seq'])
