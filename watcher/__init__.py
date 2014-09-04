import threading
import os

import cloudant


__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'
__version__ = '1.0.0'


class Watcher:
    """
    Watches a CouchDB _db_updates feed
    """

    # noinspection PyProtectedMember
    def __init__(self, host='http://localhost:5995', username=None, password=None, session_auth=True):
        self.account = cloudant.Account(host, async=False)

        if username is None:
            username = os.environ.get('COUCH_USER', '')

        if password is None:
            password = os.environ.get('COUCH_PASSWORD', '')

        if session_auth:
            r = self.account.login(username, password)
            r.raise_for_status()
        else:
            self.account._session.auth = (username, password)

        self.evt = threading.Event()
        self.thread = None

    def start(self, target=None):
        """
        Starts the watcher thread. Each db update is passed to the single-argument target callable
        as a string.

        :param target: single-argument callable
        :return:
        """

        if self.thread is not None:
            raise Exception("Cannot start a Watcher more than once")

        event = self.evt

        def callback():
            r = self.account.get('_db_updates', params={'feed': 'continuous'}, stream=True)
            r.raise_for_status()
            for update in r.iter_lines():
                if event.is_set():
                    break

                if target is not None:
                    target(update.decode('utf-8'))

            event.clear()

        self.thread = threading.Thread(target=callback, name='couch-watcher')
        self.thread.start()

    def stop(self):
        self.evt.set()
