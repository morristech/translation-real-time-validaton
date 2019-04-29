import json
from unittest.mock import MagicMock

from . import AsyncTestCase, read_fixture, AsyncContext
from notifier import const, validator, wti, stats
from notifier.model import *


class TestValidator(AsyncTestCase):
    def setUp(self):
        super().setUp()
        self.app = self.make_app()
        self.app[const.EMAIL_PROVIDER] = provider = MagicMock()
        provider.send.return_value = self.make_fut()
        self.stats_mock = MagicMock(spec=stats.Stats)
        self.stats_mock.increment.return_value = self.make_fut()
        self.app[const.STATS] = self.stats_mock

    def test_check_translations(self):
        payload = [read_fixture('payload.json', decoder=json.loads)]
        client = wti.WtiClient('dummy_api')
        self.coro(client.bootstrap())

        self.mock_session_new.request.side_effect = iter([
            AsyncContext(context=self.make_response(read_fixture('project.json'))),
            AsyncContext(context=self.make_response(read_fixture('translation_en-US.json'))),
            AsyncContext(context=self.make_response(read_fixture('users.json'))),
        ])

        self.coro(validator.check_translations(self.app, client, WtiContentTypes.md, payload, False))

    def test_check_translations_callback(self):
        payload = [read_fixture('payload.json', decoder=json.loads)]
        client = wti.WtiClient('dummy_api')
        self.coro(client.bootstrap())

        self.mock_session_new.request.side_effect = iter([
            AsyncContext(context=self.make_response(read_fixture('project.json'))),
            AsyncContext(context=self.make_response(read_fixture('translation_en-US.json'))),
            AsyncContext(context=self.make_response(read_fixture('users.json'))),
        ])
        self.coro(validator.check_translations(self.app, client, WtiContentTypes.md, payload, False, 'callback-url'))
        self.mock_session_new.post.assert_called_once()
