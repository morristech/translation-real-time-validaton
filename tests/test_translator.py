import json
from unittest.mock import MagicMock, patch

from . import AsyncTestCase, read_fixture, AsyncContext
from notifier import const, validator, wti, stats, translate
import validator as content_validator
from notifier.model import *


class TestValidator(AsyncTestCase):
    maxDiff = None

    def setUp(self):
        super().setUp()
        self.app = self.make_app()
        self.app[const.EMAIL_PROVIDER] = provider = MagicMock()
        provider.send.return_value = self.make_fut()
        self.stats_mock = MagicMock(spec=stats.Stats)
        self.stats_mock.increment.return_value = self.make_fut()
        self.app[const.STATS] = self.stats_mock

    @patch('notifier.validator.get_locales_to_translate')
    def test_translate(self, mock):
        mock.return_value = self.make_fut(['de'])
        payload = read_fixture('payload.json', decoder=json.loads)
        wti_client = wti.WtiClient('dummy_api')
        trans_client = translate.GoogleTranslateClient('dummy_api')
        fixture = read_fixture('google_translate_languages.json')
        self.mock_session_new.request.return_value = AsyncContext(context=self.make_response(body=fixture))
        self.coro(wti_client.bootstrap())
        self.coro(trans_client.bootstrap())

        self.mock_session_new.request.side_effect = iter([
            AsyncContext(context=self.make_response(read_fixture('project.json'))),
            AsyncContext(context=self.make_response(read_fixture('google_translate.json'))),
            AsyncContext(context=self.make_response()),
        ])

        self.coro(validator.machine_translate(self.stats_mock, wti_client, trans_client, payload))

    @patch('notifier.validator.get_locales_to_translate')
    def test_translating_plural(self, mock):
        mock.return_value = self.make_fut(['de'])
        payload = read_fixture('payload-plural.json', decoder=json.loads)
        wti_client = MagicMock(spec=wti.WtiClient)
        wti_client.get_project.return_value = self.make_fut(read_fixture('project.json', decoder=json.loads)['project'])
        wti_client.update_translation.return_value = self.make_fut()
        trans_client = translate.GoogleTranslateClient('dummy_api')
        fixture = read_fixture('google_translate_languages.json')
        self.mock_session_new.request.return_value = AsyncContext(context=self.make_response(body=fixture))
        self.coro(trans_client.bootstrap())

        self.mock_session_new.request.side_effect = iter([
            AsyncContext(context=self.make_response(read_fixture('google_translate.json'))),
            AsyncContext(context=self.make_response(read_fixture('google_translate.json'))),
            AsyncContext(context=self.make_response(read_fixture('google_translate.json'))),
            AsyncContext(context=self.make_response()),
        ])
        self.coro(validator.machine_translate(self.stats_mock, wti_client, trans_client, payload))
        translated_md = wti_client.update_translation.call_args[0][1]
        self.assertEqual(len(translated_md.keys()), 3)

    @patch('notifier.validator.get_locales_to_translate')
    def test_markdown_translation(self, mock):
        """
        for documenting purposes
        """
        mock.return_value = self.make_fut(['de'])
        payload = read_fixture('payload.json', decoder=json.loads)
        origin_markdown = read_fixture('markdown.md')
        wti_client = MagicMock(spec=wti.WtiClient)
        wti_client.get_project.return_value = self.make_fut(read_fixture('project.json', decoder=json.loads)['project'])
        wti_client.update_translation.return_value = self.make_fut()
        trans_client = MagicMock(spec=translate.GoogleTranslateClient)
        google_resp = read_fixture('translated_markdown.json', decoder=json.loads)
        translation = GoogleTranslation(google_resp['data']['translations'][0]['translatedText'], 'g')
        trans_client.translate.return_value = self.make_fut(translation)
        self.coro(validator.machine_translate(self.stats_mock, wti_client, trans_client, payload))
        translated_md = wti_client.update_translation.call_args[0][1]
        diff = content_validator.parse().text(origin_markdown, translated_md).html().check().md().validate()
        if len(diff):
            msg = '%s\nbase: %s,\nother: %s' % (diff[0].error_msgs, diff[0].base.diff, diff[0].other.diff)
            self.assertEqual(diff, [], msg)

    def test_get_locales_to_translate(self):
        wti_client = MagicMock(spec=wti.WtiClient)
        en_trans = read_fixture('translation_en-US.json', decoder=json.loads)
        en_trans['status'] = 'status_proofread'
        wti_client.string.side_effect = iter([
            self.make_fut(WtiString(1, 'de', 'TEXT1', WtiTranslationStatus('status_proofread'), 'DATE', False)),
            self.make_fut(WtiString(1, 'pl', 'TEXT1', WtiTranslationStatus('status_unverified'), 'DATE', False)),
            self.make_fut(WtiString(1, 'ru', 'TEXT1', WtiTranslationStatus('status_unverified'), 'DATE', False)),
            self.make_fut({})
        ])
        coro = validator.get_locales_to_translate(wti_client, 'NONE', ['de', 'pl', 'es'], validator.TRANSLATEABLE_SEG)
        got = self.coro(coro)
        self.assertCountEqual(got, ['pl', 'es'])

    def test_html_escaping(self):
        mixed_content = read_fixture('mixed-content.txt')
        escaped, placeholders = translate.mask_html_tags(mixed_content)
        unescaped = translate.unmask_html_tags(escaped, placeholders)
        unescaped2 = translate.unmask_html_tags(escaped, placeholders)
        self.assertEqual(mixed_content, unescaped)
        self.assertEqual(mixed_content, unescaped2)
