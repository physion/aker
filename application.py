import cloudant
import flask
import boto.sqs
from boto.sqs.message import Message
from flask import g

import aker


__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'

# Configuration
COUCH_HOST = 'https://ovation-io-dev.cloudant.com'
COUCH_USER = 'couch-user'
COUCH_PASSWORD = 'password'
DB_UPDATES_SQS_QUEUE = 'dev_db_updates'
REGION = 'us-east-1' # Get the region we're running in


# AWS EB requires the name application
application = app = flask.Flask(__name__)
app.config.from_object(__name__)

def _db_updates_handler(update):
    m = Message()
    m.set_body(update)
    get_queue().write(m)

_updates = aker.Watcher()  #TODO parameters

def get_queue():
    queue = getattr(g, '_queue', None)
    if queue is None:
        sqs_connection = boto.sqs.connect_to_region(app.config['REGION'])
        queue = g._queue = sqs_connection.get_queue(app.config['DB_UPDATES_SQS_QUEUE']) or sqs_connection.create_queue(app.config['DB_UPDATES_SQS_QUEUE'])
    return queue


@app.before_first_request
def start_watcher(*args, **kwargs):
    _updates.start(target=_db_updates_handler)


@app.route('/', methods=['HEAD', 'GET'])
def index():
    # You can use the context global `request` here
    return "Aker!"


@app.route('/status', methods=['GET','HEAD'])
def status():
    return flask.jsonify(queue_length = get_queue().count(),
                         running = _updates.running)

if __name__ == '__main__':
    app.run(debug=True)
