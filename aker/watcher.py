import threading
import os

import cloudant


__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'


class WatcherException(Exception):
    pass

class Watcher:
    """
    Watches a CouchDB _db_updates feed
    """

    # noinspection PyProtectedMember
    def __init__(self, host='http://localhost:5995', username=None, password=None, account_factory=cloudant.Account):


        self.account = account_factory(host, async=False)

        if username is None:
            username = os.environ.get('COUCH_USER', '')

        if password is None:
            password = os.environ.get('COUCH_PASSWORD', '')

        if host.startswith("http://localhost"):
            self.account._session.auth = (username, password)
        else:
            r = self.account.login(username, password)
            r.raise_for_status()

        self.evt = threading.Event()
        self.thread = None


    @property
    def running(self):
        """
        Checks the running status of this watcher
        :return: True if this watcher is running
        """

        return not (self.thread is None or not self.thread.is_alive())


    def start(self, target=None):
        """
        Starts the watcher thread. Each db update is passed to the single-argument target callable
        as a string.

        :param target: single-argument callable
        :return:
        """

        if self.thread is not None:
            raise WatcherException("Cannot start a Watcher more than once")

        event = self.evt

        def watch_updates():
            r = self.account.get('_db_updates', params={'feed': 'continuous'}, stream=True)
            r.raise_for_status()
            for update in r.iter_lines():
                if target is not None:
                    target(update.decode('utf-8'))

                if event.is_set():
                    break

        self.thread = threading.Thread(target=watch_updates)
        self.thread.start()

    def stop(self, timeout_seconds=None):
        self.evt.set()
        if timeout_seconds is not None:
            self.thread.join(timeout_seconds)

