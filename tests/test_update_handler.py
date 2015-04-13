import time
import unittest

import six


if six.PY3:
    from unittest.mock import MagicMock, ANY
else:
    from mock import MagicMock, ANY

import flask

from aker.handler import db_updates_handler


__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'


class UpdateHandlerTest(unittest.TestCase):
    update_line = """{"dbname": "db-94fb157e-d35e-4b2d-b14c-c2eeadfdec71", "type": "created", "account": "testy006-admin", "seq": "666-g1AAAAJAeJyN0EkKwjAUgOE4gN5CxZWbksakSVcWL6IZEakVtC5c6U30JnoTvUnNIEJdVDcvEMLHy58DAPqrjgJDJeR2pzMlcFTqfXmEMIlkvj0oXpRRocvcvmxzIAZVVa1XbT7f2IteShg2nDph9BFi2ECIoZ1i9lagV7hJEkxQfQ_WhGQOWbyRzCNUC0K5rCO0CVk65BQQAUBr7B2CoITQ1B3U4BRdO8HZHpa6uIWi8KtExQx_t4l_Stcg3ZyUegmbFFPJ_u8ToHuAHg6aeAgRMkUp_79RgJ4B8rGJh6DRtjVbvwCDzK2w"}"""

    def test_writes_db_name_message(self):
        sqs_queue = MagicMock()
        table = MagicMock()

        update = flask.json.loads(self.update_line)
        db_name = update['dbname']
        handler = db_updates_handler(sqs_queue, table)
        handler(self.update_line)

        self.assertEqual(1, sqs_queue.write.call_count)
        self.assertDictEqual({'database': db_name},
                             flask.json.loads(
                                 sqs_queue.write.call_args[0][0].get_body_encoded()))

    def test_writes_seq_to_couch(self):
        sqs_queue = MagicMock()
        database = MagicMock()
        doc = database.document.return_value = MagicMock()
        response = doc.get.return_value
        response.json.return_value = {}
        ts = time.time()
        timestamp = MagicMock(return_value=ts)

        update = flask.json.loads(self.update_line)

        handler = db_updates_handler(sqs_queue, database, timestamp=timestamp)
        handler(self.update_line)

        assert database.document.call_count > 0
        assert database.document.call_args[0][0].startswith('aker')
        doc.put.assert_called_with(params={'last_seq': update['seq'],
                                           'type': 'database-state',
                                           'database': 'aker',
                                           'timestamp': ts})

    def test_does_not_write_seq_if_write_fails(self):
        sqs_queue = MagicMock()
        db = MagicMock()
        sqs_queue.write.return_value = None

        handler = db_updates_handler(sqs_queue, db)
        handler(self.update_line)

        self.assertFalse(db.called)


    def assert_no_update_called(self, db_name, underworld_db_name):
        underworld_db_update_line = flask.json.dumps({'dbname': db_name,
                                                      'type': 'created',
                                                      'account': 'testy006-admin',
                                                      'seq': "666-g1AAAAJAeJyN0EkKwjAUgOE4gN5CxZWbksakSVcWL6IZEakVtC5c6U30JnoTvUnNIEJdVDcvEMLHy58DAPqrjgJDJeR2pzMlcFTqfXmEMIlkvj0oXpRRocvcvmxzIAZVVa1XbT7f2IteShg2nDph9BFi2ECIoZ1i9lagV7hJEkxQfQ_WhGQOWbyRzCNUC0K5rCO0CVk65BQQAUBr7B2CoITQ1B3U4BRdO8HZHpa6uIWi8KtExQx_t4l_Stcg3ZyUegmbFFPJ_u8ToHuAHg6aeAgRMkUp_79RgJ4B8rGJh6DRtjVbvwCDzK2w"})
        sqs_queue = MagicMock()
        db = MagicMock()
        db_result = db.get.return_value
        db_result.json.return_value = {'db_name': underworld_db_name}

        handler = db_updates_handler(sqs_queue, db)
        handler(underworld_db_update_line)
        self.assertFalse(sqs_queue.write.called)

    def test_does_not_send_update_if_underworld_db(self):
        self.assert_no_update_called("underworld_db", "underworld_db")

    def test_does_not_send_update_for_team_db(self):
        self.assert_no_update_called("team-123", "underworld_db")

    def test_does_not_send_update_for__replicator_db(self):
        self.assert_no_update_called("_replicator", "underword_db")
