import os

__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'

import flask

app = flask.Flask(__name__)


@app.route('/')
def hello_world():
    # use request here
    return "Hello world!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
