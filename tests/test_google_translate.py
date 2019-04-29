from . import AsyncTestCase, read_fixture, AsyncContext

from notifier import translate
from notifier.model import *


class TestGoogleTranslate(AsyncTestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.client = translate.GoogleTranslateClient('API_KEY')
        self.coro(self.client.bootstrap())

    def test_translate(self):
        fixture = read_fixture('google_translate.json')
        expected = GoogleTranslation('Witaj świecie', 'nmt')
        self.mock_session_new.request.return_value = AsyncContext(context=self.make_response(body=fixture))
        actual = self.coro(self.client.translate('Hello world', 'en', 'pl'))
        self.assertEqual(expected, actual)
