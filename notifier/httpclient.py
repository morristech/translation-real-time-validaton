import aiohttp
import asyncio
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class RetryLimit(aiohttp.ClientError):
    def __init__(self, parent_ex):
        self.status = getattr(parent_ex, 'status', None)
        self.message = getattr(parent_ex, 'message', None)


class HttpClient(object):
    def __init__(self, host, *args, loop=None, max_wait=0, max_retries=1, **kwargs):
        self._host = host
        self._loop = loop or asyncio.get_event_loop()
        self._max_wait = max_wait
        self._max_retries = max_retries
        self._retry_delay = 3
        self._max_follow_links = 10
        self._session = aiohttp.ClientSession(*args, loop=self._loop, **kwargs)

    async def bootstrap(self):
        self._session = await self._session.__aenter__()

    async def close(self):
        if not self._session.closed:
            await self._session.close()

    def _next_page_link(self, headers):
        header = headers.get('Link')
        if header:
            for link in header.split(','):
                bits = link.split(';')
                if bits[1].strip() == 'rel="next"':
                    return bits[0].strip('<>')
        return None

    async def _request(self, method, url, **kwargs):
        if self._max_wait > 0:
            kwargs.setdefault('timeout', self._max_wait)
        async with self._session.request(method, url, **kwargs) as res:
            if 'application/json' in res.headers['CONTENT-TYPE'].lower():
                data = await res.json()
            else:
                data = await res.text()
            # this is almost like raise_for_status, except it reads response from server and attaches it to exception
            if 400 <= res.status:
                raise aiohttp.ClientResponseError(
                    res.request_info,
                    res.history,
                    status=res.status,
                    message='%s : %s' % (res.reason, data),
                    headers=res.headers)
            return data

    async def _request_pages(self, method, url, follow_counter=1, **kwargs):
        data = []
        if self._max_wait > 0:
            kwargs.setdefault('timeout', self._max_wait)
        async with self._session.request(method, url, **kwargs) as res:
            res.raise_for_status()
            if 'application/json' in res.headers['CONTENT-TYPE'].lower():
                data.extend(await res.json())
            next_page = self._next_page_link(res.headers)
            if next_page and follow_counter < self._max_follow_links:
                next_page_data = await self._request_pages(method, next_page, follow_counter + 1, **kwargs)
                data.extend(next_page_data)
            return data

    async def _request_and_retry(self, req_method, *args, max_wait=0, max_retries=1, **kwargs):
        retry_limit = max_retries if max_retries > 1 else int(self._max_retries)
        retry = 0
        while retry < retry_limit:
            retry += 1
            try:
                data = await req_method(*args, timeout=max_wait, **kwargs)
                return data
            except aiohttp.ClientError as ex:
                # retry only for 5xx or connection errors
                status = getattr(ex, 'status', 500)
                if status < 500:
                    raise
                if retry < retry_limit:
                    await asyncio.sleep(self._retry_delay * (retry + 1))
                else:
                    raise RetryLimit(ex) from ex

    async def request(self, method, path, *args, max_wait=0, max_retries=1, follow_links=False, **kwargs):
        url = urljoin(self._host, path.lstrip('/'))
        req_method = self._request_pages if follow_links else self._request
        if self._max_retries > 1 or max_retries > 1:
            res = await self._request_and_retry(req_method,
                                                method, url, *args, max_wait=max_wait, max_retries=max_retries,
                                                **kwargs)
        else:
            res = await req_method(method, url, *args, timeout=max_wait, **kwargs)
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
