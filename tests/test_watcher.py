import threading
import unittest
from unittest.mock import MagicMock

import requests

from watcher import Watcher, WatcherException


__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'

#TODO mock watcher.account so that we don't actually have to call _db_updates or login

class WatcherTest(unittest.TestCase):

    def setUp(self):
        self.account_factory = MagicMock()
        self.account = MagicMock()
        self.account_factory.return_value = self.account

        # For get('_db_updates')
        response = MagicMock()
        response.iter_lines.return_value = [b'line1', b'line2']
        self.account.get.return_value = response


    def test_should_throw_exception_for_failed_login(self):

        response = MagicMock()
        response.status_code = 401
        self.account.login.side_effect = requests.HTTPError(response=response)

        self.assertRaises(requests.HTTPError,
                          lambda: Watcher('https://aker.cloudant.com', 'foo', 'bar', account_factory=self.account_factory))

    def test_should_log_in(self):
        Watcher('http://myhost.com', 'username', 'password', account_factory=self.account_factory)

        self.account_factory.assert_called_with('http://myhost.com', async=False)
        self.account.login.assert_called_with('username', 'password')

    def test_should_support_request_auth(self):
        self.account._session = MagicMock()

        Watcher('http://localhost', username='username', password='password', account_factory=self.account_factory)

        self.assertEqual(('username', 'password'), self.account._session.auth)

    def test_should_throw_exception_starting_more_than_once(self):

        watcher = Watcher('http://localhost:5995',
                          username='foo',
                          password='foopass',
                          account_factory=self.account_factory)

        watcher.start()
        try:
            self.assertRaises(WatcherException, lambda: watcher.start())
        finally:
            watcher.stop(timeout_seconds=0.5)
            self.assertFalse(watcher.thread.is_alive())

    def test_should_watch_changes(self):
        watcher = Watcher('http://localhost:5995',
                          username='username',
                          password='password',
                          account_factory=self.account_factory)

        evt = threading.Event()

        def update_handler(update):
            evt.set()

        watcher.start(target=update_handler)

        try:
            TIMEOUT_SECONDS = 0.5
            self.assertTrue(evt.wait(timeout=TIMEOUT_SECONDS))
            self.account.get.assert_called_with('_db_updates', params={'feed':'continuous'}, stream=True)
        finally:
            watcher.stop(timeout_seconds=1.0)
            self.assertFalse(watcher.thread.is_alive())

