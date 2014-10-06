import os
import logging

import cloudant
import flask
import boto.sqs
import boto.exception
from flask import g
import requests

import aker
from aker.couch import login


__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'



# AWS EB requires the name application
application = app = flask.Flask(__name__)
app.config.from_object(aker.default_settings)
if 'AKER_CONFIG_PATH' in os.environ:
    app.config.from_envvar('AKER_CONFIG_PATH')

# Check environment variables and override
config_overrides = ['COUCH_HOST', 'COUCH_USER', 'COUCH_PASSWORD',
                    'DB_UPDATES_SQS_QUEUE', 'SECRET_KEY', 'UNDERWORLD_DATABASE']
for k in config_overrides:
    if k in os.environ:
        app.config[k] = os.environ[k]


# Configure logging
if not app.config['TESTING']:
    pass
    #logging.basicConfig(filename='/opt/python/log/aker.log',level=logging.DEBUG)


def get_queue():
    queue = getattr(g, 'aker_queue', None)
    if queue is None:
        sqs_connection = boto.sqs.connect_to_region(app.config['REGION'])
        queue = g.aker_queue = sqs_connection.get_queue(app.config['DB_UPDATES_SQS_QUEUE']) or sqs_connection.create_queue(
            app.config['DB_UPDATES_SQS_QUEUE'])
    return queue

def get_database(account_factory=None):
    if account_factory is None:
        account_factory = cloudant.Account

    database = getattr(g, app.config['UNDERWORLD_DATABASE'], None)
    if database is None:
        account = login(host=app.config['COUCH_HOST'],
                        username=app.config['COUCH_USER'],
                        password=app.config['COUCH_PASSWORD'],
                        async=False,
                        account_factory=account_factory)

        database = g.underworld_database = account.database(app.config['UNDERWORLD_DATABASE'])
        # r = database.get()
        # if r.status_code == requests.codes.NOT_FOUND:
        #     database.put().raise_for_status()

        return database


logging.info("Configuring Watcher for {}".format(app.config['COUCH_HOST']))
_updates = aker.Watcher(host=app.config['COUCH_HOST'],
                        username=app.config['COUCH_USER'],
                        password=app.config['COUCH_PASSWORD'])

@app.before_first_request
def start_watcher(*args, **kwargs):
    logging.info("Starting updates watcher...")
    _updates.start(target=aker.handler.db_updates_handler(queue=get_queue(), database=get_database()))


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
    try:
        database = get_database()
        doc = database.document('aker')
        r = doc.get()
        r.raise_for_status()
        worker_state = r.json()
        last_seq = worker_state['last_seq']
    except:
        last_seq = "0"

    return flask.jsonify(queue_length=get_queue().count(),
                         running=_updates.running,
                         version=aker.__version__,
                         last_seq=last_seq)


if __name__ == '__main__':
    app.run(debug=True)
