from unittest.mock import MagicMock

from notifier import mailer, const
from notifier.model import *
from validator.errors import *
from . import AsyncTestCase


class TestMailer(AsyncTestCase):
    def setUp(self):
        super().setUp()
        self.app = self.make_app()
        self.app[const.EMAIL_PROVIDER] = self.provider = MagicMock()
        self.provider.send.return_value = self.make_fut()
        self.user = WtiUser('dummy_id', 'dummy_email', WtiUserRoles.translator)

    def test_send_happy_path(self):
        diff = DiffError(None, None, 'section link')
        self.coro(mailer.send(self.app, self.user, diff))
        html = self.provider.send.call_args[0][1]
        self.assertTrue('class="section-link"' in html)

    def test_url_errors(self):
        url = UrlDiff('dummy_url', [], 404)
        diff = DiffError([url], None, 'section link')
        self.coro(mailer.send(self.app, self.user, diff))
        html = self.provider.send.call_args[0][1]
        self.assertTrue('class="url-errors"' in html)

    def test_md_error(self):
        base = ContentData('original1', 'parsed1', 'diff1')
        other = ContentData('original2', 'parsed2', 'diff2')
        md = MdDiff(base, other, [])
        diff = DiffError(None, md, 'section link')
        self.coro(mailer.send(self.app, self.user, diff))
        html = self.provider.send.call_args[0][1]
        self.assertTrue('class="diff"' in html)


class TestProvider(AsyncTestCase):
    def setUp(self):
        super().setUp()
        self.provider = mailer.SendgridProvider({
            'sendgrid.user': 'user',
            'sendgrid.password': 'password',
            'from.email': 'from email',
            'from.name': 'from name',
            'email.subject': 'subject'
        })

    def test_happy_path(self):
        self.coro(self.provider.send('test@test.com', 'html'))
        self.assertTrue(self.mock_session_new.post.called)
