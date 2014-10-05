import logging
import os

import cloudant


def login(host='http://localhost:5995',
          username=None,
          password=None,
          account_factory=cloudant.Account,
          async=False):

    account = account_factory(host, async=async)

    if username is None:
        username = os.environ.get('COUCH_USER', '')

    if password is None:
        password = os.environ.get('COUCH_PASSWORD', '')

    if host.startswith("http://localhost"):
        logging.info("Configuring Watcher for Authentication auth")
        account._session.auth = (username, password)
    else:
        logging.info("Configuring Watcher for session auth")
        r = account.login(username, password)
        r.raise_for_status()

    return account
