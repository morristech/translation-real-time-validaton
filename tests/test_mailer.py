from unittest.mock import MagicMock, patch
from notifier import mailer
from collections import namedtuple

from . import AsyncTestCase


class TestMailer(AsyncTestCase):

    @patch('aiohttp.request')
    def test_send_happy_path(self, mock_req):
        user = {'email': 'test@test.com'}
        Error = namedtuple('Error', ['base', 'other', 'diff', 'base_path', 'other_path'])
        error = Error._make(['base', 'other', 'diff', 'base_path', 'other_path'])
        mailer.send('url', user, error, 'md')
