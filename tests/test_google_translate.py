from . import AsyncTestCase, read_fixture, AsyncContext

from notifier import translate
from notifier.model import *


class TestGoogleTranslate(AsyncTestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.client = translate.GoogleTranslateClient('API_KEY')
        fixture = read_fixture('google_translate_languages.json')
        self.mock_session_new.request.return_value = AsyncContext(context=self.make_response(body=fixture))
        self.coro(self.client.bootstrap())

    def test_translate(self):
        fixture = read_fixture('google_translate.json')
        expected = GoogleTranslation('Witaj świecie', 'nmt')
        self.mock_session_new.request.return_value = AsyncContext(context=self.make_response(body=fixture))
        actual = self.coro(self.client.translate('Hello world', 'en', 'pl'))
        self.assertEqual(expected, actual)

    def test_translate_fallback_to_major_locale(self):
        fixture = read_fixture('google_translate.json')
        self.mock_session_new.request.return_value = AsyncContext(context=self.make_response(body=fixture))
        url = 'https://translation.googleapis.com/language/translate/v2/languages'
        data = {'target': 'en', 'model': 'nmt', 'key': 'API_KEY'}
        self.mock_session_new.request.assert_called_with('GET', url, params=data, timeout=0)
