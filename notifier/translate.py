import logging

import aiohttp

from . import httpclient
from .model import *

logger = logging.getLogger(__name__)


class TranslationError(aiohttp.ClientError):
    def __init__(self, parent_ex, req_params):
        self.status = getattr(parent_ex, 'status', None)
        self.message = getattr(parent_ex, 'message', None)
        self.req_params = req_params

    def __repr__(self):
        return 'Translator failed, status: %s, message: %s, params: %s' % (self.status, self.message, self.req_params)


class UnknownResponse(Exception):
    def __init__(self, resp_data):
        self.resp_data = resp_data

    def __repr__(self):
        return 'Unknown response format: %s' % self.resp_data


class GoogleTranslateClient:
    HOST = 'https://translation.googleapis.com/language/translate/v2'

    def __init__(self, api_key, model='nmt'):
        self._api_key = api_key
        self._model = model
        self._client = httpclient.HttpClient(self.HOST, max_retries=3)

    async def shutdown(self):
        await self._client.close()

    async def bootstrap(self):
        await self._client.bootstrap()

    async def translate(self, text, source_locale, target_locale, fmt='text'):
        params = {
            'q': text,
            'target': target_locale,
            'source': source_locale,
            'format': fmt,
            'model': self._model,
            'key': self._api_key
        }
        try:
            resp = await self._client.post('', data=params)
        except aiohttp.ClientResponseError as ex:
            raise TranslationError(ex, params)
        try:
            translation = resp['data']['translations'][0]
        except KeyError:
            raise UnknownResponse(resp)
        return GoogleTranslation(**translation)

    async def languages(self):
        params = {
            'target': 'en',
            'model': self._model,
            'key': self._api_key
        }
        resp = await self._client.get('', data=params)
        languages = resp['data']['languages']
        return languages
