import unittest

from application import app

__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'


class FlaskTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def test_index(self):
        rv = self.app.get('/')
        self.assertEqual(200, rv._status_code)

if __name__ == '__main__':
    unittest.main()
