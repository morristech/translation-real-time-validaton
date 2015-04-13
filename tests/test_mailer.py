from unittest.mock import MagicMock, patch
from notifier import mailer
from collections import namedtuple

from . import AsyncTestCase


class TestMailer(AsyncTestCase):

    @patch('mandrill.Mandrill')
    def test_send_happy_path(self, mock_mandrill):
        mock_send = mock_mandrill.return_value.messages.send
        user = {'email': 'test@test.com'}
        Error = namedtuple('Error', ['base', 'other', 'diff', 'base_path', 'other_path'])
        error = Error._make(['base', 'other', 'diff', 'base_path', 'other_path'])
        mailer.send('key', user, error)
