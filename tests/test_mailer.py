from unittest.mock import MagicMock
from notifier import mailer, segment, validators

from . import AsyncTestCase


class TestMailer(AsyncTestCase):

    def test_send_happy_path(self):
        mock_client = MagicMock()
        mock_client.send.return_value = self.make_fut(MagicMock(status=200))
        diff_error = validators.DiffError('<h1>a</h1>', '<h2>b</h2>', '#a', '##b', ['message'])
        url_error = validators.UrlError('http://noope', 404, False)
        translation = segment.TranslationSegment(string_id=1, status=None,
                                                 content_type='md',
                                                 locale='pl', content='<ins>##b</ins>',
                                                 base_locale='en', base_content='<del>#a</del>',
                                                 filename='filename', filename_ext='txt',
                                                 project_id=2, project_name='Example',
                                                 user_id=1, user_email='a@example.com', user_role=None,
                                                 diff_errors=[diff_error], url_errors=[url_error])

        self.coro(mailer.send(mock_client, 'email', [translation], 'md'))
