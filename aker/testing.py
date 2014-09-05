import unittest

from application import app


__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'


class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass
