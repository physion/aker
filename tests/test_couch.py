import json
import six

if six.PY3:
    from unittest.mock import patch, MagicMock
else:
    from mock import patch, MagicMock

import aker.couch as couch
from aker.testing import FlaskTestCase


__copyright__ = 'Copyright (c) 2014. Physion LLC. All rights reserved.'


class TestApp(FlaskTestCase):

    def test_gets_last_seq(self):
        db = MagicMock()
        ddoc = db.design.return_value
        idx = ddoc.view.return_value
        last_seq = 123
        full_seq = str(last_seq) + "-abc"
        response = idx.get.return_value = MagicMock()
        response.json.return_value = {'rows': [{'key': 'aker', 'value': [last_seq, full_seq]}]}

        r = couch.last_seq(db)

        self.assertEqual(full_seq, r)
        idx.get.assert_called_with(params={'keys': ['aker'], 'group': True})
