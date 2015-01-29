import os
import notifier
from notifier import const
import json
from unittest.mock import MagicMock, patch

from . import AsyncTestCase


def read(path):
    with open(os.path.join('tests/fixtures', path)) as fp:
        return json.load(fp)


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
        req.post.return_value = self.make_fut(read('wti_hook.json'))
        req.app = {
            const.MASTER_LOCALE: 'en',
            const.WTI_KEY: 'wti_key',
            const.MANDRILL_KEY: 'mandrill_key',
            const.ASYNC_WORKER: MagicMock()
        }
        mock_json = MagicMock()
        mock_json.json.return_value = self.make_fut({
            'text': '#bbbb'
        })
        mock_users = MagicMock()
        mock_users.json.return_value = self.make_fut([{'user_id': 19362, 'email': 'test@test.com'}])
        mock_get.side_effect = iter([self.make_fut(mock_json), self.make_fut(mock_users)])

        res = self.coro(notifier.new_translation(req))

        self.assertEqual(200, res.status)
        self.assertFalse(mock_mailer.send.called)


class TestProject(AsyncTestCase):

    @patch('aiohttp.request')
    def test_project(self, mock_get):
        req = MagicMock()
        req.post.return_value = self.make_fut({'email': 'test@test.com'})
        req.match_info = {'api_key': 'key'}
        res = MagicMock()
        res.json.side_effect = iter([
            self.make_fut(read('project.json')),
            self.make_fut(read('strings.json')),
            self.make_fut(read('translation_en-US.json')),
            self.make_fut(read('translation_pl.json'))
        ])
        mock_get.return_value = self.make_fut(res)

        actual = self.coro(notifier.project(req))

        self.assertEqual(200, actual.status)
