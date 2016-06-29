from unittest.mock import patch, MagicMock
from notifier import mailer
from collections import namedtuple

from . import AsyncTestCase


class TestMailer(AsyncTestCase):

    @patch('aiohttp.request')
    def test_send_happy_path(self, mock_req):
        mock_req.side_effect = self.make_fut('')
        user = {'email': 'test@test.com'}
        diff_base = namedtuple('DiffBase', ['parsed', 'diff'])('parsed', 'diff')
        diff = namedtuple('Diff', ['base', 'other', 'error_msgs'])(diff_base, diff_base, ['error'])
        DiffError = namedtuple('DiffError', ['base', 'other', 'diff', 'base_path',
                                             'other_path', 'file_path', 'section_link'])
        diff_error = DiffError('base', 'other', diff, 'base_path',
                               'other_path', 'file_path', 'section_link')

        UrlError = namedtuple('UrlError', ['url', 'status_code', 'section_link', 'file_path', 'locale'])
        url_error = UrlError('url', 'status_code', 'section_link', 'file', 'locale')

        self.coro(mailer.send('url', user, [diff_error], [url_error], 'md'))
