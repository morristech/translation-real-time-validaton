import asyncio
import logging

from . import const, compare
from .model import *

logger = logging.getLogger(__name__)


def _to_dc_items(wti_items, zendesk_items):
    return [DynamicContentItem(key, wti_items.get(key), zendesk_item) for key, zendesk_item in zendesk_items.items()]


async def _get_all_translations(zendesk_dc, wti_client, dc_item, zendesk_locales):
    tasks = [
        wti_client.string(dc_item.wti_id, locale) for locale in zendesk_locales if locale != zendesk_dc.default_locale
    ]
    data = await asyncio.gather(*tasks)
    return [d for d in data if d]


def _default_translation(translations, default_locale):
    for translation in translations:
        if translation.locale == default_locale:
            return translation.text
    return ''


async def _update_item(zendesk_dc, wti_client, zendesk_locales, dc_item):
    res = False
    translations = await _get_all_translations(zendesk_dc, wti_client, dc_item, zendesk_locales)
    if compare.is_different(_default_translation(translations, zendesk_dc.default_locale), dc_item.zendesk_item.text):
        logger.info('updating wti item with key:%s', dc_item.key)
        await wti_client.update_translation(dc_item, zendesk_dc.default_locale, translations)
        res = True
    else:
        logger.debug('item with key %s did not change', dc_item.key)
    logger.info('updating dynamic content key:%s for locales:%s', dc_item.key,
                list(map(lambda i: i.locale, translations)))
    await zendesk_dc.update(dc_item, translations, zendesk_locales)
    return res


async def _create_item(zendesk_dc, wti_client, zendesk_locales, dc_item):
    logger.info('creating new wti item with key:%s', dc_item.key)
    await wti_client.create_string(dc_item, zendesk_dc.default_locale)
    return True


async def sync_zendesk(app):
    zendesk_dc = app[const.ZENDESK_DC]
    wti_client = app[const.WTI_DYNAMIC_CONTENT]
    stats = app[const.STATS]

    wti_items = await wti_client.strings_ids()
    if not wti_items:
        logger.error('no wti strings found')
        return
    zendesk_locales = await zendesk_dc.locales()
    zendesk_items = await zendesk_dc.items(zendesk_locales)
    dc_items = _to_dc_items(wti_items, zendesk_items)
    logger.info('get %s items to process', len(dc_items))
    updated_keys = []
    for dc_item in dc_items:
        if dc_item.wti_id:
            res = await _update_item(zendesk_dc, wti_client, zendesk_locales, dc_item)
            if res:
                updated_keys.append(dc_item.key)
        else:
            await _create_item(zendesk_dc, wti_client, zendesk_locales, dc_item)
            updated_keys.append(dc_item.key)
    if updated_keys:
        await app[const.SLACK_NOTIFIER].notify(updated_keys)
        stats.increment('sync_items', len(updated_keys))
    logger.info('done updating content')
