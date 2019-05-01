import logging
import aiohttp
import json
import asyncio
import re

from . import compare, mailer, const
from .model import *

logger = logging.getLogger(__name__)
UPDATE_PATH = 'admin/refresh_wti'


def mask_markdown_urls(text):
    placeholder = 'K33P'
    regex = r"\((http?.*)\)"
    mask = []

    def replace(match):
        mask.append(text[match.span(1)[0]:match.span(1)[1]])
        return '(%s)' % placeholder

    try:
        masked_text = re.sub(regex, replace, text)
        return mask, masked_text
    except TypeError:
        logger.exception('text = %s', text)


def unmask_markdown(masked_text, masked):
    regex = r"\((K33P)\)"
    masked = masked.copy()
    masked.reverse()

    def replace(match):
        return '(%s)' % masked.pop()

    unmasked_text = re.sub(regex, replace, masked_text)

    return unmasked_text


async def machine_translate(wti_client, translate_client, data):
    wti_translation = data['translation']
    project = await wti_client.get_project()
    string_id = wti_translation.get('string').get('id')
    logger.info('Auto translating, stringId: %s, for project: %s', string_id, project.get('name'))
    text = wti_translation.get('text')
    if not text:
        logger.info('Skipping auto translation for empty source text, stringId: %s', string_id)
    source_locale_code = project.get('source_locale').get('code')
    target_locales = filter(lambda locale: locale.get('code') != source_locale_code, project.get('target_locales', []))
    masked, masked_text = mask_markdown_urls(text)
    for target_locale in target_locales:
        target_locale_code = target_locale.get('code')
        translated = await translate_client.translate(masked_text, wti_translation.get('locale'), target_locale_code)
        unmasked_translated = unmask_markdown(translated.translatedText, masked)
        await wti_client.update_translation(string_id, unmasked_translated, target_locale_code, False)
        logger.info('Updated translation %s -> %s', target_locale_code, string_id)
    return


async def callback(callback_url, data, is_successful):
    logger.debug('notifying external service via callback url = %s', callback_url)
    translation_data = {
        'payload': data,
        'validation_successful': is_successful
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(callback_url, data=json.dumps(translation_data)) as resp:
            try:
                if resp.status >= 400:
                    raise aiohttp.ClientResponseError(resp.status)
            except aiohttp.ClientResponseError:
                logger.exception('Could not notify external service via callback: %s', callback_url)


async def check_translations(app, wti_client, content_type, payload, machine_translation, callback_url=None):
    logger.info('translating %s segments', len(payload))
    for data in payload:
        if data['translation'].get('locale').lower() == 'en' and machine_translation:
            asyncio.ensure_future(app[const.STATS].increment('translations'))
            await machine_translate(wti_client, app[const.TRANSLATE_CLIENT], data)
            asyncio.ensure_future(app[const.STATS].increment('translations.succeeded'))
            continue
        if data['translation'].get('status') != WtiTranslationStatus.proofread.value:
            continue
        logger.debug('translating %s', data)
        is_successful = await _check_translation(app, wti_client, content_type, data)
        if callback_url:
            asyncio.ensure_future(callback(callback_url, data, is_successful))


async def _check_translation(app, wti_client, content_type, translation):
    project = await wti_client.project(translation['file_id'], content_type)
    base_string = await wti_client.string(translation['string_id'], project.master_locale)
    translation_status = WtiTranslationStatus(translation['translation'].get('status'))
    translated_string = WtiString(translation['string_id'], translation['locale'], translation['translation']['text'],
                                  translation_status)
    diff = await app.loop.run_in_executor(None, compare.diff, wti_client, project, base_string, translated_string)
    if diff and (diff.url_errors or diff.md_error):
        logger.info('errors found in string %s, project %s', translation['string_id'], translation['project_id'])
        user = await wti_client.user(translation['user_id'])
        if user.email is None:
            email = app[const.APP_SETTINGS].get('email.admin')
        else:
            email = user.email
        await mailer.send(app, email, diff)
        asyncio.ensure_future(app[const.STATS].increment('validations.failed'))
        if user.role != WtiUserRoles.manager:
            await wti_client.change_status(translated_string)
        return False
    else:
        asyncio.ensure_future(app[const.STATS].increment('validations.succeeded'))
        return True
