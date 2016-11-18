import asyncio
import logging

from . import const
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


async def _update_item(zendesk_dc, wti_client, zendesk_locales, dc_item):
    await wti_client.update_translation(dc_item, zendesk_dc.default_locale)
    translations = await _get_all_translations(zendesk_dc, wti_client, dc_item, zendesk_locales)
    logger.info('updating dynamic content key:%s for locales:%s', dc_item.key,
                list(map(lambda i: i.locale, translations)))
    await zendesk_dc.update(dc_item, translations, zendesk_locales)


async def _create_item(zendesk_dc, wti_client, zendesk_locales, dc_item):
    logger.info('creating new item in wti key:%s', dc_item.key)
    await wti_client.create_string(dc_item, zendesk_dc.default_locale)


async def sync_zendesk(app):
    zendesk_dc = app[const.ZENDESK_DC]
    wti_client = app[const.WTI_DYNAMIC_CONTENT]

    wti_items = await wti_client.strings_ids()
    if not wti_items:
        logger.error('no wti strings found')
        return
    logger.info('got %s trings', len(wti_items))
    zendesk_locales = await zendesk_dc.locales()
    zendesk_items = await zendesk_dc.items(zendesk_locales)
    dc_items = _to_dc_items(wti_items, zendesk_items)
    for dc_item in dc_items:
        if dc_item.wti_id:
            await _update_item(zendesk_dc, wti_client, zendesk_locales, dc_item)
        else:
            await _create_item(zendesk_dc, wti_client, zendesk_locales, dc_item)
