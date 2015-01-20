from unittest.mock import MagicMock, patch
from notifier import mailer
from validator.reports import MarkdownError

from . import AsyncTestCase


class TestMailer(AsyncTestCase):

    @patch('mandrill.Mandrill')
    def test_send_happy_path(self, mock_mandrill):
        mock_send = mock_mandrill.return_value.messages.send
        user = {'email': 'test@test.com'}
        error = MarkdownError('base', 'other', 'diff')
        error.base_path = 'base_path'
        error.other_path = 'other_path'
        mailer.send('key', user, error)
