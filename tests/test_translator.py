import json
from unittest.mock import MagicMock

from . import AsyncTestCase, read_fixture, AsyncContext
from notifier import const, validator, wti, stats, translate


class TestValidator(AsyncTestCase):
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
        self.coro(wti_client.bootstrap())
        self.coro(trans_client.bootstrap())

        self.mock_session_new.request.side_effect = iter([
            AsyncContext(context=self.make_response(read_fixture('project.json'))),
            AsyncContext(context=self.make_response(read_fixture('google_translate.json'))),
            AsyncContext(context=self.make_response()),
        ])

        self.coro(validator.machine_translate(wti_client, trans_client, payload))
