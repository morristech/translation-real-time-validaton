from unittest.mock import patch
from . import AsyncTestCase
from notifier import compare


class TestCompare(AsyncTestCase):
    def test_diff_happy_path(self):
        actual = self.coro(compare.diff('aaa', 'aaa'))
        self.assertIsNone(actual)

    def test_diff_same_structure(self):
        actual = self.coro(compare.diff('##aaa\n\naaa', '##bbb\n\nbbb'))
        self.assertIsNone(actual)

    def test_diff_different_structure(self):
        actual = self.coro(compare.diff('##aaa\n\naaa', '#bbb\n\nbbb'))
        self.assertIsNotNone(actual)
