import asyncio
import os
import simplejson as json
from unittest import TestCase
from unittest.mock import MagicMock, patch, Mock

from notifier import const


def read_fixture(filename, mode='r', decoder=None):
    filepath = os.path.join('tests/fixtures', filename)
    with open(filepath, mode) as fp:
        content = fp.read()
        if decoder:
            return decoder(content)
        else:
            return content


class AppMock(object):
    def __init__(self, loop):
        self.loop = loop
        self._dict = {}

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, value):
        self._dict[key] = value
        return value

    def get(self, key, default=None):
        if key not in self._dict:
            return default
        return self._dict[key]

    def set(self, key, value):
        self._dict[key] = value
        return value


class AsyncContext(Mock):
    def __init__(self, *args, context=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._context = context

    async def __aenter__(self):
        return self._context

    async def __aexit__(self, exc_type, exc, tb):
        pass


class AsyncTestCase(TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.res = MagicMock()
        self.res.status = 200
        self.res.read.return_value = self.make_fut(b'', )

        self.mock_request_patch = patch('aiohttp.request')
        self.mock_request = self.mock_request_patch.start()
        self.mock_request.return_value = AsyncContext(context=self.make_response())

        self.mock_session_patch = patch('aiohttp.ClientSession')
        self.mock_session = self.mock_session_patch.start()
        self.mock_session_new = MagicMock(name='new session')
        self.mock_session_response = self.make_response()
        self.mock_session_req = AsyncContext(name='session.<request> context', context=self.mock_session_response)
        self.mock_session_new.get.return_value = self.mock_session_req
        self.mock_session_new.post.return_value = self.mock_session_req
        self.mock_session_new.request.return_value = self.mock_session_req
        self.mock_session.return_value = AsyncContext(name='new aiohttp.ClientSession context',
                                                      context=self.mock_session_new)
        # self.mock_session_post = self.mock_session().__aenter__().post
        # self.mock_session_post.return_value = self.make_res()
        # self.mock_session_get = self.mock_session().__aenter__().get
        # self.mock_session_get.return_value = self.make_res()
        # self.mock_session_request = self.mock_session().__aenter__().request
        # self.mock_session_request.return_value = self.make_res()

        self.mock_wait_patch = patch('asyncio.wait_for')
        self.mock_wait = self.mock_wait_patch.start()

        self.mock_sleep_patch = patch('asyncio.sleep')
        self.mock_sleep = self.mock_sleep_patch.start()

    def tearDown(self):
        self.loop.close()
        self.mock_request_patch.stop()
        self.mock_session_patch.stop()
        self.mock_wait_patch.stop()
        self.mock_sleep_patch.stop()

    def coro(self, coro):
        return self.loop.run_until_complete(coro)

    def make_fut(self, result='', exception=None):
        fut = asyncio.Future(loop=self.loop)
        if exception:
            fut.set_exception(exception)
        else:
            fut.set_result(result)
        return fut

    def make_res(self, body='', status=200, headers=None):
        resp = self.make_response(body, status, headers)
        return self.make_fut(resp)

    def make_response(self, body='', status=200, headers=None):
        res = MagicMock()
        res.status = status
        res.headers = headers or {}
        res.read.return_value = self.make_fut(body.encode('utf-8'))
        res.json.return_value = self.make_fut(json.loads(body or '{}'))
        res.release.return_value = self.make_fut()
        return res

    def make_res_json(self, body={}, status=200):
        return self.make_res(json.dumps(body), status)

    def make_req(self, get_params=None, post_params=None):
        req = MagicMock()
        req.post.return_value = self.make_fut(post_params or {})
        req.GET = get_params or {}
        return req

    def make_app(self, settings=None):
        settings = settings or {}
        app = AppMock(self.loop)
        app[const.APP_SETTINGS] = settings
        return app
