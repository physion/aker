__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'

import flask

# AWS EB requires the name application
application = app = flask.Flask(__name__)

@app.route('/')
def index():
    # use request here
    return "Hello world!"

if __name__ == '__main__':
    app.run(debug=True)
