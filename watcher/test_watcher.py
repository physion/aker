import os
import threading
import unittest

from watcher import Watcher


__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'


class WatcherTest(unittest.TestCase):

    def test_should_throw_exception_for_failed_login(self):
        self.assertRaises(Exception, lambda: Watcher('ovation-io-dev','foo', 'bar'))

    def test_should_throw_exception_starting_more_than_once(self):
        watcher = Watcher('http://localhost:5995',
                          username=os.environ['COUCH_USER'],
                          password=os.environ['COUCH_PASSWORD'],
                          session_auth=False)

        watcher.start()
        self.assertRaises(Exception, lambda: watcher.start())


    def test_should_watch_changes(self):
        watcher = Watcher(username=os.environ['COUCH_USER'],
                          password=os.environ['COUCH_PASSWORD'],
                          session_auth=False)

        evt = threading.Event()
        def update_handler(update):
            evt.set()

        watcher.start(target=update_handler)

        evt.wait(5)
        watcher.stop()

        TIMEOUT_SECONDS = 5
        self.assertTrue(evt.wait(timeout=TIMEOUT_SECONDS))
