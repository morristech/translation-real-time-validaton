from . import AsyncTestCase
from unittest.mock import MagicMock

import notifier

class TestHealthcheck(AsyncTestCase):
    def test_happy_path(self):
        req = MagicMock()
        res = self.coro(notifier.healthcheck(req))
        self.assertEqual(200, res.status)


class TestNewTranslation(AsyncTestCase):
    def test_happy_path(self):
        req = MagicMock()
        res = self.coro(notifier.new_translation(req))
        self.assertEqual(200, res.status)
