import unittest


__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'


class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        from application import app

        app.config['TESTING'] = True
        self.app = app.test_client()


    def tearDown(self):
        pass
