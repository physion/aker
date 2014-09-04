import unittest

__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'


class WatcherTest(unittest.TestCase):

    def test_fails(self):
        self.fail("I should fail")
