import logging

import aiohttp

from . import httpclient
from .model import *

logger = logging.getLogger(__name__)


class GoogleTranslateClient:
    HOST = 'https://translation.googleapis.com/language/translate/v2/'

    def __init__(self, api_key, model='nmt'):
        self._api_key = api_key
        self._model = model
        self._languages = []
        self._client = httpclient.HttpClient(self.HOST, max_retries=3)

    async def shutdown(self):
        await self._client.close()

    async def bootstrap(self):
        await self._client.bootstrap()
        self._languages = list(await self.languages())

    def map_locale(self, locale):
        # try exact match en-US == en-US
        google_locale = filter(lambda l: l.language.lower() == locale.lower(), self._languages)
        try:
            google_locale = list(google_locale)[0]
            return google_locale.language
        except IndexError:
            # try fuzzy match en-* == en
            if len(locale) > 2:
                return self.map_locale(locale[0:2])
            raise UnsupportedLocale(locale)

    async def translate(self, text, source_locale, target_locale, fmt='text'):
        s_locale = self.map_locale(source_locale)
        t_locale = self.map_locale(target_locale)

        params = {
            'q': text,
            'target': t_locale,
            'source': s_locale,
            'format': fmt,
            'model': self._model,
            'key': self._api_key
        }
        try:
            resp = await self._client.post('', params=params)
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
        try:
            resp = await self._client.get('/languages', params=params)
        except aiohttp.ClientResponseError as ex:
            raise TranslationError(ex, params)
        try:
            languages = resp['data']['languages']
        except KeyError:
            raise UnknownResponse(resp)
        return (GoogleLanguage(**language) for language in languages)
