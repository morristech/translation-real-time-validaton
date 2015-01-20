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
    def test_new_translation(self, mock_get):
        req = MagicMock()
        req.json.return_value = self.make_fut(json.loads(read('wti_hook.json')))
        req.app = {const.MASTER_LOCALE: 'en'}
        mock_get.text.return_value = self.make_fut('Are you sure you want to delete this comment?')

        res = self.coro(notifier.new_translation(req))

        self.assertEqual(200, res.status)
