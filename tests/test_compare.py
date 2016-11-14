from unittest.mock import MagicMock

from . import AsyncTestCase
from notifier import compare
from notifier.model import *


class TestCompare(AsyncTestCase):
    def setUp(self):
        super().setUp()
        self.client = MagicMock()
        self.client.section_link.return_value = 'dummy_link'

    def test_strings(self):
        project = WtiProject('dummy_id', 'dummy_name', 'dummy_locale', 'file.strings', WtiContentTypes.ios)
        base = WtiString('id1', 'aaa http://www.link.com aaa', 'locale1')
        other = WtiString('id2', 'aaa', 'locale2')
        compare.diff(self.client, project, base, other)
        self.assertFalse(self.mock_request.called)

    def _test_ios_text(self):
        project = WtiProject('dummy_id', 'dummy_name', 'dummy_locale', 'file.txt', WtiContentTypes.ios)
        base = WtiString('id1', 'aaa http://www.link.com aaa', 'locale1')
        other = WtiString('id2', 'aaa', 'locale2')
        return compare.diff(self.client, project, base, other)

    def test_ios_txt_success(self):
        self._test_ios_text()
        self.mock_request.assert_called_once_with('get', 'http://www.link.com', headers={})

    def test_ios_txt_fail(self):
        self.mock_request.return_value = self.make_res(status=404)
        errors = self._test_ios_text()
        self.assertEqual(1, len(errors.url_errors))

    def _test_md(self, other):
        project = WtiProject('dummy_id', 'dummy_name', 'dummy_locale', 'file.md', WtiContentTypes.md)
        base = WtiString('id1', 'aaa\n\naaa', 'locale1')
        return compare.diff(self.client, project, base, other)

    def test_md_success(self):
        other = WtiString('id2', 'bbb\n\nbbb', 'locale2')
        errors = self._test_md(other)
        self.assertIsNone(errors.md_error)

    def test_md_fail(self):
        other = WtiString('id2', 'bbb\nbbb', 'locale2')
        errors = self._test_md(other)
        self.assertIsNotNone(errors.md_error)
