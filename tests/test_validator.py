import json
from unittest.mock import MagicMock

from . import AsyncTestCase, read_fixture, AsyncContext
from notifier import const, validator, wti
from notifier.model import *


class TestValidator(AsyncTestCase):
    def test_check_translations(self):
        app = self.make_app()
        app[const.EMAIL_PROVIDER] = provider = MagicMock()
        app[const.STATS] = MagicMock()
        provider.send.return_value = self.make_fut()

        payload = [read_fixture('payload.json', decoder=json.loads)]
        client = wti.WtiClient('dummy_api')

        self.mock_session_new.get.side_effect = iter([
            AsyncContext(name='session.<request> context', context=self.make_response(read_fixture('project.json'))),
            AsyncContext(name='session.<request> context', context=self.make_response(read_fixture('translation_en-US.json'))),
            AsyncContext(name='session.<request> context', context=self.make_response(read_fixture('users.json'))),
        ])

        self.coro(validator.check_translations(app, client, WtiContentTypes.md, payload))
