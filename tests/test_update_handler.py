import unittest
from unittest.mock import MagicMock

import flask
from boto.sqs.message import Message

from aker.handler import db_updates_handler


__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'

class UpdateHandlerTest(unittest.TestCase):

    update_line = """{"dbname": "documentationchangescontinuous1documentation94fb157e-d35e-4b2d-b14c-c2eeadfdec71", "type": "created", "account": "testy006-admin", "seq": "666-g1AAAAJAeJyN0EkKwjAUgOE4gN5CxZWbksakSVcWL6IZEakVtC5c6U30JnoTvUnNIEJdVDcvEMLHy58DAPqrjgJDJeR2pzMlcFTqfXmEMIlkvj0oXpRRocvcvmxzIAZVVa1XbT7f2IteShg2nDph9BFi2ECIoZ1i9lagV7hJEkxQfQ_WhGQOWbyRzCNUC0K5rCO0CVk65BQQAUBr7B2CoITQ1B3U4BRdO8HZHpa6uIWi8KtExQx_t4l_Stcg3ZyUegmbFFPJ_u8ToHuAHg6aeAgRMkUp_79RgJ4B8rGJh6DRtjVbvwCDzK2w"}"""

    def test_writes_message(self):
        sqs_queue = MagicMock()
        table = MagicMock()
        m = Message()
        m.set_body(self.update_line)

        handler = db_updates_handler(sqs_queue, table)
        handler(self.update_line)

        self.assertEqual(1, sqs_queue.write.call_count)
        self.assertEqual(flask.json.loads(self.update_line),
                         sqs_queue.write.call_args[0][0]._body)


    def test_writes_seq_to_dynamo(self):
        sqs_queue = MagicMock()
        table = MagicMock()
        aker_item = MagicMock()
        table.get_item.return_value = aker_item
        update = flask.json.loads(self.update_line)

        handler = db_updates_handler(sqs_queue, table)
        handler(self.update_line)

        aker_item.__setitem__.assert_called_with('last_seq', update["seq"])
        aker_item.partial_save.assert_called_with()

    def test_does_not_write_seq_if_write_fails(self):
        sqs_queue = MagicMock()
        table = MagicMock()
        sqs_queue.write.return_value = None

        handler = db_updates_handler(sqs_queue, table)
        handler(self.update_line)

        self.assertFalse(table.called)