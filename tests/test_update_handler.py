import unittest

import six


if six.PY3:
    from unittest.mock import MagicMock
else:
    from mock import MagicMock

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
                            flask.json.loads(sqs_queue.write.call_args[0][0]._body))

    def test_writes_seq_to_couch(self):
        sqs_queue = MagicMock()
        database = MagicMock()
        doc = database.document.return_value = MagicMock()
        response = doc.get.return_value
        response.json.return_value = {}

        update = flask.json.loads(self.update_line)

        handler = db_updates_handler(sqs_queue, database)
        handler(self.update_line)

        database.document.assert_called_with('aker')
        doc.put.assert_called_with({'last_seq': update['seq']})

    def test_does_not_write_seq_if_write_fails(self):
        sqs_queue = MagicMock()
        db = MagicMock()
        sqs_queue.write.return_value = None

        handler = db_updates_handler(sqs_queue, db)
        handler(self.update_line)

        self.assertFalse(db.called)

