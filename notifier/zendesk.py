import aiohttp
import logging

from . import httpclient
from .model import *

logger = logging.getLogger(__name__)


class ZendeskDynamicContent:
    HOST = 'https://keepsafe.zendesk.com/api/v2/'
    LOCALES_PATH = 'locales.json'
    ITEMS_PATH = 'dynamic_content/items.json'
    MANY_VARIANTS_PATH = 'dynamic_content/items/%s/variants/update_many.json'

    def __init__(self, settings):
        self._settings = settings
        user = settings['zendesk.user']
        token = settings['zendesk.token']
        headers = {
            'Authorization': aiohttp.BasicAuth('{}/token'.format(user), token).encode(),
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        self._client = httpclient.HttpClient(self.HOST, headers=headers)
        self.default_locale = settings.get('zendesk.default_locale', 'en-US')
        self._locales_mapping = {}

    async def _get_data(self, path):
        logger.debug('getting data from zendesk path:%s', path)
        res = await self._client.get(path)
        if res.status == 200:
            data = await res.json()
            return data
        else:
            await res.release()
            raise ZendeskError('unable to get data from zendesk path:%s, status:%s' % (path, res.status))

    async def locales(self):
        data = await self._get_data(self.LOCALES_PATH)
        return {locale['locale']: locale['id'] for locale in data['locales']}

    def _extract_key(self, item):
        key = item['placeholder']
        return key.strip('{}')

    def _extract_item(self, item, zendesk_locales):
        variants = {}
        text = ''
        for variant_item in item['variants']:
            if variant_item['locale_id'] == zendesk_locales[self.default_locale]:
                text = variant_item['content']
            else:
                locale_id = variant_item['locale_id']
                variants[locale_id] = variant_item['id']
        if not text:
            logger.error('no variant for locale %s and item %s', locale_id, item['id'])
        return ZendeskItem(item['id'], text, variants)

    async def items(self, zendesk_locales):
        data = await self._get_data(self.ITEMS_PATH)
        items = data['items']
        result = {}
        for item in items:
            key = self._extract_key(item)
            result[key] = self._extract_item(item, zendesk_locales)
        return result

    async def update(self, dc_item, translations, zendesk_locales):
        variants = []
        for translation in translations:
            locale_id = zendesk_locales[translation.locale]
            if locale_id in dc_item.zendesk_item.variants:
                translation_id = dc_item.zendesk_item.variants[locale_id]
                variants.append({'id': translation_id, 'active': True, 'default': False, 'content': translation.text})
            else:
                logger.warning('missing variant for locale id:%s name:%s', locale_id, translation.locale)
        path = self.MANY_VARIANTS_PATH % dc_item.zendesk_item.id
        res = await self._client.put(path, {'variants': variants})
        if res.status not in [200, 201]:
            msg = await res.read()
            logger.error('unable to update zendesk content status: %s, message: %s', status, msg)
        await res.release()
