import aiohttp
import logging
import json

from . import httpclient
from .model import *

logger = logging.getLogger(__name__)


class ZendeskDynamicContent:
    HOST = 'https://keepsafe.zendesk.com/api/v2/'
    LOCALES_PATH = 'locales.json'
    ITEMS_PATH = 'dynamic_content/items.json'
    UPDATE_MANY_PATH = 'dynamic_content/items/%s/variants/update_many.json'
    CREATE_MANY_PATH = 'dynamic_content/items/%s/variants/create_many.json'

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

    async def shutdown(self):
        await self._client.close()

    async def _get_data(self, path):
        logger.debug('getting data from zendesk path:%s', path)
        res = await self._client.get(path)
        if res.status == 200:
            data = await res.json()
            return data
        else:
            await res.release()
            logger.error('unable to get data from zendesk path:%s, status:%s', path, res.status)
            return {}

    async def _put_data(self, path, data, method='PUT'):
        res = await self._client.request(method, path, data=json.dumps(data, sort_keys=True))
        if res.status not in [200, 201]:
            msg = await res.read()
            logger.error('unable to update zendesk content status: %s, message: %s', res.status, msg)
            return False
        await res.release()
        return True

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
        return ZendeskItem(item['id'], item['name'], text, variants)

    async def items(self, zendesk_locales):
        next_page = self.ITEMS_PATH
        result = {}
        for i in range(15):
            data = await self._get_data(next_page)
            items = data['items']
            for item in items:
                key = self._extract_key(item)
                result[key] = self._extract_item(item, zendesk_locales)
            next_page = data.get('next_page')
            if not next_page:
                break
        logger.debug('got %s items from zendesk', len(result))
        return result

    async def update(self, dc_item, translations, zendesk_locales):
        update_variants = []
        create_variants = []
        for translation in translations:
            locale_id = zendesk_locales[translation.locale]
            variant = {'locale_id': locale_id, 'active': True, 'default': False, 'content': translation.text}
            if locale_id in dc_item.zendesk_item.variants:
                variant['id'] = dc_item.zendesk_item.variants[locale_id]
                update_variants.append(variant)
            else:
                create_variants.append(variant)
        if update_variants:
            path = self.UPDATE_MANY_PATH % dc_item.zendesk_item.id
            await self._put_data(path, {'variants': update_variants})
        if create_variants:
            path = self.CREATE_MANY_PATH % dc_item.zendesk_item.id
            await self._put_data(path, {'variants': create_variants}, 'POST')
