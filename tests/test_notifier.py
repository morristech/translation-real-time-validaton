import os
import notifier
from notifier import const
import json
from unittest.mock import MagicMock, patch

from . import AsyncTestCase


def read(path):
    with open(os.path.join('tests/fixtures', path)) as fp:
        return fp.read()


class TestHealthcheck(AsyncTestCase):

    def test_happy_path(self):
        req = MagicMock()
        res = self.coro(notifier.healthcheck(req))
        self.assertEqual(200, res.status)


class TestNewTranslation(AsyncTestCase):

    @patch('aiohttp.request')
    @patch('notifier.mailer')
    def test_new_translation(self, mock_mailer, mock_get):
        req = MagicMock()
        req.json.return_value = self.make_fut(json.loads(read('wti_hook.json')))
        req.app = {
            const.MASTER_LOCALE: 'en',
            const.WTI_KEY: 'wti_key',
            const.MANDRILL_KEY: 'mandrill_key'
        }
        mock_json = MagicMock()
        mock_json.json.return_value = self.make_fut({
            'text': 'Are you sure you want to delete this comment?'
        })
        mock_users = MagicMock()
        mock_users.json.return_value = self.make_fut([{'id': 123, 'email': 'test@test.com'}])
        mock_get.side_effect = iter([self.make_fut(mock_json), self.make_fut(mock_users)])

        res = self.coro(notifier.new_translation(req))

        self.assertEqual(200, res.status)
        self.assertFalse(mock_mailer.send.called)
