import flask
from boto.sqs.message import Message
import requests

__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'


def db_updates_handler(queue=None, database=None):
    """
    Makes an update handler for the given SQS queue

    :param queue: SQS queue
    :param database: DynamoDB table for last sequence
    :return: _db_updates_handler function
    """

    def update_handler(line):
        """
        Handles a single line of _db_updates. Update lines have the form::

            {
              "dbname": "documentationchangescontinuous1documentation94fb157e-d35e-4b2d-b14c-c2eeadfdec71",
              "type": "created",
              "account": "testy006-admin",
              "seq": "666-g1AAAAJAeJyN0EkKwjAUgOE4gN5CxZWbksakSVcWL6IZEakVtC5c6U30JnoTvUnNIEJdVDcvEMLHy58DAPqrjgJDJeR2pzMlcFTqfXmEMIlkvj0oXpRRocvcvmxzIAZVVa1XbT7f2IteShg2nDph9BFi2ECIoZ1i9lagV7hJEkxQfQ_WhGQOWbyRzCNUC0K5rCO0CVk65BQQAUBr7B2CoITQ1B3U4BRdO8HZHpa6uIWi8KtExQx_t4l_Stcg3ZyUegmbFFPJ_u8ToHuAHg6aeAgRMkUp_79RgJ4B8rGJh6DRtjVbvwCDzK2w"
            }

        Sends the update to the SQS specified by `get_queue` and then records the seq in Couch.

        :param line: _db_updates line
        :return: None
        """
        update = flask.json.loads(line)
        seq = update['seq']

        m = Message()
        msg_body = {'database': update['dbname']}
        m.set_body(flask.json.dumps(msg_body))
        sent_message = queue.write(m)

        if sent_message:
            doc = database.document('aker')

            r = doc.get()
            if r.status_code == requests.codes.NOT_FOUND:
                worker_state = {'last_seq': str(seq)}
            else:
                worker_state = r.json()
                worker_state['last_seq'] = str(seq)


            doc.put(params=worker_state).raise_for_status()

    return update_handler



