import os

from boto.dynamodb2.table import Table
from boto.dynamodb2.fields import HashKey, RangeKey
import flask
import boto.sqs
import boto.exception
from flask import g

import aker

__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'


# AWS EB requires the name application
application = app = flask.Flask(__name__)
app.config.from_object(aker.default_settings)
if 'AKER_CONFIG_PATH' in os.environ:
    app.config.from_envvar('AKER_CONFIG_PATH')

# Check environment variables and override
config_overrides = ['COUCH_HOST', 'COUCH_USER', 'COUCH_PASSWORD',
                    'DB_UPDATES_SQS_QUEUE', 'SECRET_KEY']
for k in config_overrides:
    if k in os.environ:
        app.config[k] = os.environ[k]



def get_queue():
    queue = getattr(g, 'aker_queue', None)
    if queue is None:
        sqs_connection = boto.sqs.connect_to_region(app.config['REGION'])
        queue = g.aker_queue = sqs_connection.get_queue(app.config['DB_UPDATES_SQS_QUEUE']) or sqs_connection.create_queue(
            app.config['DB_UPDATES_SQS_QUEUE'])
    return queue

def get_last_seq_table():
    table = getattr(app, 'aker_last_seq_table', None)
    if table is None:
        t = boto.dynamodb2.table.Table(app.config['UNDERWORLD_TABLE'])
        try:
            t.describe()
        except boto.exception.JSONResponseError:
            t = boto.dynamodb2.table.Table.create(app.config['UNDERWORLD_TABLE'],
                             schema=[
                                 HashKey('worker'),
                                 RangeKey('last_seq')
                             ])
        table = app.aker_last_seq_table = t

    return table


_updates = aker.Watcher(host=app.config['COUCH_HOST'],
                        username=app.config['COUCH_USER'],
                        password=app.config['COUCH_PASSWORD'])

@app.before_first_request
def start_watcher(*args, **kwargs):
    _updates.start(target=aker.handler.db_updates_handler(queue=get_queue(), table=get_last_seq_table()))


@app.errorhandler(aker.WatcherException)
def handle_watcher_exception(error):
    response = flask.jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/', methods=['HEAD', 'GET'])
def index():
    # You can use the context global `request` here
    if not _updates.running:
        raise aker.WatcherException("Updates watcher not running", status_code=500, payload={'error': 'Updates watcher not running'})

    return "Aker!"


@app.route('/status', methods=['GET', 'HEAD'])
def status():
    return flask.jsonify(queue_length=get_queue().count(),
                         running=_updates.running,
                         version=aker.__version__,
                         last_seq=get_last_seq_table().get_item(worker='aker')['last_seq'])


if __name__ == '__main__':
    app.run(debug=True)
