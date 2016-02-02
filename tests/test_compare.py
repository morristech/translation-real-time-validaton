from unittest.mock import patch
from . import AsyncTestCase
from notifier import compare


class TestCompareMd(AsyncTestCase):
    def test_diff_happy_path(self):
        actual = self.coro(compare.diff('aaa', 'aaa'))
        self.assertEqual([], actual)

    def test_diff_same_structure(self):
        actual = self.coro(compare.diff('##aaa\n\naaa', '##bbb\n\nbbb'))
        self.assertEqual([], actual)

    def test_diff_different_structure(self):
        actual = self.coro(compare.diff('##aaa\n\naaa', '#bbb\n\nbbb'))
        self.assertNotEqual([], actual)


class TestCompatreJava(AsyncTestCase):
    def test_diff_happy_path(self):
        actual = self.coro(compare.diff('aaa', 'aaa', 'java'))
        self.assertEqual([], actual)

    def test_diff_happy_path(self):
        actual = self.coro(compare.diff('aaa', 'aaa', 'java'))
        self.assertEqual([], actual)
