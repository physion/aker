import threading
import logging

import cloudant
from requests import HTTPError

from aker.couch import login


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
                 account_factory=cloudant.Account,
                 since="0"):

        self.account = login(host=host,
                             username=username,
                             password=password,
                             account_factory=account_factory,
                             async=False)

        self.since_seq = since


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

        if self.thread is not None and self.thread.is_alive():
            logging.error("Attempted to start a Watcher that is already running")
            return


        event = self.evt

        def watch_updates():

            logging.info("Getting _db_updates since {}".format(self.since_seq))

            r.raise_for_status()
            for update in r.iter_lines():
                if target is not None:
                    try:
                        u = update.decode('utf-8')
                        logging.info("Processing update {}", u)
                        target(u)
                    except HTTPError as ex:
                        logging.error("Unable to process update", ex)

                if event.is_set():
                    break

        self.thread = threading.Thread(target=watch_updates)
        self.thread.start()

    def stop(self, timeout_seconds=None):
        self.evt.set()
        if timeout_seconds is not None:
            self.thread.join(timeout_seconds)

