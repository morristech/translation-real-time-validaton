import aiohttp
import asyncio
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class FakeResponse(object):
    def __init__(self, status):
        self.status = status

    @asyncio.coroutine
    def read(self):
        return b''

    @asyncio.coroutine
    def text(self):
        return ''

    @asyncio.coroutine
    def json(self):
        return {}

    @asyncio.coroutine
    def release(self):
        pass


class TimeoutResponse(FakeResponse):
    def __init__(self):
        super().__init__(504)


class ErrorResponse(FakeResponse):
    def __init__(self):
        super().__init__(500)


class HttpClient(object):
    def __init__(self, host, *args, loop=None, success_codes=(200, 201, 400), max_wait=0, max_retries=1, **kwargs):
        self._host = host
        self._loop = loop or asyncio.get_event_loop()
        self._max_wait = max_wait
        self._max_retries = max_retries
        self._success_codes = success_codes
        self._session = aiohttp.ClientSession(*args, loop=self._loop, **kwargs)

    async def bootstrap(self):
        self._session = await self._session.__aenter__()

    async def _request(self, method, url, *args, **kwargs):
        if self._max_wait > 0:
            kwargs.setdefault('timeout', self._max_wait)
        try:
            async with self._session.request(method, url, *args, **kwargs) as res:
                return res
        except aiohttp.client_exceptions.ServerTimeoutError:
            return TimeoutResponse()
        except (aiohttp.client_exceptions.ClientOSError, aiohttp.client_exceptions.ClientResponseError,
                aiohttp.ClientConnectionError):
            logger.exception('unable to connect to client url:%s', url)
            return ErrorResponse()

    async def _request_and_retry(self, *args, success_codes=tuple(), max_wait=0, max_retries=1, **kwargs):
        retries = max_retries if max_retries > 1 else int(self._max_retries)
        success_codes = success_codes if success_codes else self._success_codes
        res = None
        while retries > 0:
            retries -= 1
            if res:
                res = await self._request(*args, timeout=max_wait, **kwargs)
            if res.status in success_codes:
                return res
        return res

    async def request(self, method, path, *args, success_codes=tuple(), max_wait=0, max_retries=1, **kwargs):
        url = urljoin(self._host, path.lstrip('/'))
        if self._max_retries > 1 or max_retries > 1:
            res = await self._request_and_retry(
                method, url, *args, success_codes=success_codes, max_wait=max_wait, max_retries=max_retries, **kwargs)
        else:
            res = await self._request(method, url, *args, timeout=max_wait, **kwargs)
        return res

    async def get(self, path, *args, **kwargs):
        res = await self.request('GET', path, *args, **kwargs)
        return res

    async def post(self, path, *args, **kwargs):
        res = await self.request('POST', path, *args, **kwargs)
        return res

    async def put(self, path, *args, **kwargs):
        res = await self.request('PUT', path, *args, **kwargs)
        return res

    async def delete(self, path, *args, **kwargs):
        res = await self.request('DELETE', path, *args, **kwargs)
        return res

    async def head(self, path, *args, **kwargs):
        res = await self.request('HEAD', path, *args, **kwargs)
        return res

    async def patch(self, path, *args, **kwargs):
        res = await self.request('PATCH', path, *args, **kwargs)
        return res

    async def options(self, path, *args, **kwargs):
        res = await self.request('OPTIONS', path, *args, **kwargs)
        return res

    async def close(self):
        await self._session.close()
