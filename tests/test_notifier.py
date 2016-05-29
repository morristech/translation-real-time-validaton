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

    def _test(self, mock_get, text, req_query_params=None, wti_keys=None):
        req = MagicMock()
        req.post.return_value = self.make_fut(read('wti_hook.json'))
        req.GET = {'app': 'test_app'} if req_query_params is None else req_query_params
        req.app = {
            const.WTI_KEYS: {'test_app': 'wti_key'} if wti_keys is None else wti_keys,
            const.MANDRILL_KEY: 'mandrill_key',
            const.ASYNC_WORKER: worker.Worker(self.loop),
            const.EMAIL_CMS: 'url',
            const.MAILMAN: 'url'
        }

        mock_res = MagicMock()
        mock_res.json.side_effect = iter([
            self.make_fut(read('project.json')),
            self.make_fut([{'user_id': 1, 'email': 'test@test.com'}]),
            self.make_fut({'text': text}),
        ])
        mock_res.status = 200
        mock_get.return_value = self.make_fut(mock_res)

        return self.coro(notifier.new_translation(req))

    @patch('aiohttp.request')
    @patch('notifier.mailer.send')
    @patch('notifier.tasks.translate.change_status')
    def test_success(self, mock_status, mock_mailer, mock_get):
        res = self._test(mock_get, '#aaaaa')

        self.assertEqual(200, res.status)
        self.assertFalse(mock_mailer.called)
        self.assertFalse(mock_status.called)

    @patch('aiohttp.request')
    @patch('notifier.tasks.mailer.send')
    @patch('notifier.tasks.translate.change_status')
    def test_fail(self, mock_status, mock_mailer, mock_get):
        res = self._test(mock_get, '##bbbb')

        self.assertEqual(200, res.status)
        self.assertTrue(mock_mailer.called)
        self.assertTrue(mock_status.called)

    @patch('aiohttp.request')
    def test_no_wti_app_in_query_string(self, mock_get):
        res = self._test(mock_get, '', {})
        self.assertEqual(400, res.status)

    @patch('aiohttp.request')
    def test_no_key_for_wti_app(self, mock_get):
        res = self._test(mock_get, '', wti_keys={})
        self.assertEqual(400, res.status)

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
