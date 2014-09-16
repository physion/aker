import threading
import os
import logging

import cloudant


__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'


class WatcherException(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class Watcher:
    """
    Watches a CouchDB _db_updates feed
    """

    PROCESS = 'aker'
    LAST_SEQ = 'last_seq'

    # noinspection PyProtectedMember
    def __init__(self, host='http://localhost:5995',
                 username=None,
                 password=None,
                 account_factory=cloudant.Account):

        self.account = account_factory(host, async=False)
        self.last_seq_table = None

        if username is None:
            username = os.environ.get('COUCH_USER', '')

        if password is None:
            password = os.environ.get('COUCH_PASSWORD', '')

        if host.startswith("http://localhost"):
            logging.info("Configuring Watcher for Authentication auth")
            self.account._session.auth = (username, password)
        else:
            logging.info("Configuring Watcher for session auth")
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


    def start(self, target=None, last_seq_table=None):
        """
        Starts the watcher thread. Each db update is passed to the single-argument target callable
        as a string.

        :param target: single-argument callable
        :param last_seq_table: dynamodb2.table.Table for storing last_seq information
        :return:
        """

        if self.thread is not None:
            logging.error("Attempted to start a Watcher that is already running")
            raise WatcherException("Cannot start a Watcher more than once")

        self.last_seq_table = last_seq_table

        event = self.evt

        def watch_updates():
            item = self.last_seq_table.get_item(worker=self.PROCESS,
                                                attributes=[self.LAST_SEQ]) if self.last_seq_table else None
            last_seq = item[self.LAST_SEQ] if item else '0'

            logging.info("Getting _db_updates since {}".format(last_seq))

            r = self.account.get('_db_updates', params={'feed': 'continuous', 'since': last_seq}, stream=True)
            r.raise_for_status()
            for update in r.iter_lines():
                if target is not None:
                    try:
                        target(update.decode('utf-8'))
                    finally:
                        pass  # Update last_seq

                if event.is_set():
                    break

        self.thread = threading.Thread(target=watch_updates)
        self.thread.start()

    def stop(self, timeout_seconds=None):
        self.evt.set()
        if timeout_seconds is not None:
            self.thread.join(timeout_seconds)

