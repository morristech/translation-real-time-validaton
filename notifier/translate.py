import logging
import re

import aiohttp

from . import httpclient
from .model import *

logger = logging.getLogger(__name__)


def mask_html_tags(text):
    """
    Escapes html tags in a way that is going to be useful for using google translate with fmt = html
    Unfortunately html.escape won't work
    Each tag gets substituted with placeholder $$IDX$$ where IDX is number,
    :param text:
    :return:
    """
    def repl(match):
        placeholders.append(match.group(0))
        return '$${}$$'.format(len(placeholders) - 1)

    placeholders = []
    html_tag_regex = r"<.*?>"
    masked = re.sub(html_tag_regex, repl, text)
    return masked, placeholders


def unmask_html_tags(text, placeholders):
    def repl(match):
        tag = p.pop(0)
        return tag

    p = placeholders.copy()
    placeholder_regex = r"\$\$\s?\d*\s?\$\$"
    unescaped = re.sub(placeholder_regex, repl, text)
    return unescaped


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

    def map_locale(self, locale: str):
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
        except Exception:
            logger.exception('Something went wrong, requested locale: %s, available: %s', locale,
                             ', '.join((lang.language for lang in self._languages)))

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
