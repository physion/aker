import logging
import flask
from boto.sqs.message import RawMessage
import requests
import uuid

__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'


def db_updates_handler(queue=None, database=None):
    """
    Makes an update handler for the given SQS queue

    :param queue: SQS queue
    :param database: CouchDB database for underworld state
    :return: _db_updates_handler function
    """

    underworld_db_name = database.get().json()['db_name']

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

        SQS message contains {'database': update['dbname'} as a JSON-encoded string. E.g.
            {"database": "team-90979670-2a11-0132-bf70-22000a7bab2e"}
             => '{"database": "team-90979670-2a11-0132-bf70-22000a7bab2e"}'

        :param line: _db_updates line
        :return: None
        """
        update = flask.json.loads(line)
        seq = update['seq']

        logging.info("[Aker] Update received for database {dbname}".format(**update))

        if (update['dbname'] != underworld_db_name) and \
                (update['dbname']!='_replicator') and \
                (not update['dbname'].startswith('team-')) and \
                (update['dbname'] != underworld_db_name + "_dev"):
            msg_body = {'database': update['dbname']}
            m = RawMessage(body=flask.json.dumps(msg_body))

            logging.info("[Aker] Sending message to queue {}".format(m))
            sent_message = queue.write(m)

            if sent_message:
                doc = database.document('aker-' + str(uuid.uuid4()))

                worker_state = {'last_seq': str(seq),
                                'type': 'database-state',
                                'database': 'aker'}

                doc.put(params=worker_state).raise_for_status()

    return update_handler



