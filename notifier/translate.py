import logging

from . import httpclient
from .model import *

logger = logging.getLogger(__name__)


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
        resp = await self._client.post('', data=params)
        translation = resp['data']['translations'][0]
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
