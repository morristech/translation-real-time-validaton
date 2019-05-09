import json
from unittest.mock import MagicMock

from . import AsyncTestCase, read_fixture, AsyncContext
from notifier import const, validator, wti, stats, translate, model
import validator as content_validator


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

    def test_translate(self):
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

        self.coro(validator.machine_translate(wti_client, trans_client, payload))

    def test_markdown_translation(self):
        """
        for documenting purposes
        """
        payload = read_fixture('payload.json', decoder=json.loads)
        origin_markdown = read_fixture('markdown.md')
        wti_client = MagicMock(spec=wti.WtiClient)
        wti_client.get_project.return_value = self.make_fut(read_fixture('project.json', decoder=json.loads)['project'])
        wti_client.update_translation.return_value = self.make_fut()
        trans_client = MagicMock(spec=translate.GoogleTranslateClient)
        google_resp = read_fixture('translated_markdown.json', decoder=json.loads)
        translation = model.GoogleTranslation(google_resp['data']['translations'][0]['translatedText'], 'g')
        trans_client.translate.return_value = self.make_fut(translation)
        self.coro(validator.machine_translate(wti_client, trans_client, payload))
        translated_md = wti_client.update_translation.call_args[0][1]
        diff = content_validator.parse().text(origin_markdown, translated_md).html().check().md().validate()
        if len(diff):
            msg = '%s\nbase: %s,\nother: %s' % (diff[0].error_msgs, diff[0].base.diff, diff[0].other.diff)
            self.assertEqual(diff, [], msg)
