import os
import notifier
from notifier import const, worker
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

    def _test(self, mock_get, text):
        req = MagicMock()
        req.post.return_value = self.make_fut(read('wti_hook.json'))
        req.app = {
            const.WTI_KEY: 'wti_key',
            const.MANDRILL_KEY: 'mandrill_key',
            const.ASYNC_WORKER: worker.Worker(self.loop)
        }

        mock_res = MagicMock()
        mock_res.json.side_effect = iter([
            self.make_fut(read('project.json')),
            self.make_fut({'text': text}),
            self.make_fut([{'user_id': 1, 'email': 'test@test.com'}]),
        ])
        mock_get.return_value = self.make_fut(mock_res)

        return self.coro(notifier.new_translation(req))

    @patch('aiohttp.request')
    @patch('notifier.mailer')
    @patch('notifier.tasks.translate.change_status')
    def test_success(self, mock_status, mock_mailer, mock_get):
        res = self._test(mock_get, '''##PIN timeout
Do you go in and out of KeepSafe frequently? [Premium makes this safer and faster](http://support.getkeepsafe.com/hc/articles/204056310).

Activate PIN timeout and KeepSafe stays unlocked for 30 seconds after you leave the app. If you come back within that time, you won’t have to enter your PIN.
''')

        self.assertEqual(200, res.status)
        self.assertFalse(mock_mailer.send.called)
        self.assertFalse(mock_status.called)

    @patch('aiohttp.request')
    @patch('notifier.tasks.mailer')
    @patch('notifier.tasks.translate.change_status')
    def test_fail(self, mock_status, mock_mailer, mock_get):
        res = self._test(mock_get, '##bbbb')

        self.assertEqual(200, res.status)
        self.assertTrue(mock_mailer.send.called)
        self.assertTrue(mock_status.called)


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
