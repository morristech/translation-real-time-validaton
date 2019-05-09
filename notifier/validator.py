import logging
import aiohttp
import json
import asyncio
import markdown
import html2text

from . import compare, mailer, const
from .model import *

logger = logging.getLogger(__name__)
UPDATE_PATH = 'admin/refresh_wti'


async def machine_translate(wti_client, translate_client, data):
    html2text_conv = html2text.HTML2Text()
    html2text_conv.body_width = 0
    wti_translation = data['translation']
    project = await wti_client.get_project()
    string_id = wti_translation.get('string').get('id')
    logger.info('Auto translating, stringId: %s, for project: %s', string_id, project.get('name'))
    text = wti_translation.get('text')
    if not text:
        logger.info('Skipping auto translation for empty source text, stringId: %s', string_id)
    source_locale_code = project.get('source_locale').get('code')
    target_locales = filter(lambda locale: locale.get('code') != source_locale_code, project.get('target_locales', []))
    html_text = markdown.markdown(text)
    for target_locale in target_locales:
        target_locale_code = target_locale.get('code')
        try:
            translated = await translate_client.translate(html_text, wti_translation.get('locale'), target_locale_code,
                                                          'html')
            translated_md = html2text_conv.handle(translated.translatedText)
            await wti_client.update_translation(string_id, translated_md, target_locale_code, False)
            logger.info('Updated translation %s -> %s', target_locale_code, string_id)
        except Exception:
            sentry_tags = {
                'project': project.get('name'),
                'string_id': string_id,
                'target_locale': target_locale_code
            }
            logger.error('Could not update translation', extra=sentry_tags)
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
            try:
                await machine_translate(wti_client, app[const.TRANSLATE_CLIENT], data)
                asyncio.ensure_future(app[const.STATS].increment('translations.succeeded'))
            except Exception:
                logger.exception('Failed to auto translate: %s', data)
            continue
        if data['translation'].get('status') != WtiTranslationStatus.proofread.value:
            continue
        logger.debug('validating %s', data)
        try:
            is_successful = await _check_translation(app, wti_client, content_type, data)
            if callback_url:
                asyncio.ensure_future(callback(callback_url, data, is_successful))
        except Exception:
            project = await wti_client.get_project()
            sentry_tags = {
                'project': project.get('name'),
                'content_type': content_type,
                'string_id': data['translation'].get('string').get('id'),
            }
            logger.exception('Could not validate translation', extra=sentry_tags)


async def _check_translation(app, wti_client, content_type, translation):
    project = await wti_client.project(translation['file_id'], content_type)
    base_string = await wti_client.string(translation['string_id'], project.master_locale)
    translation_status = WtiTranslationStatus(translation['translation'].get('status'))
    translated_string = WtiString(translation['string_id'], translation['locale'], translation['translation']['text'],
                                  translation_status, translation['translation']['updated_at'])
    diff = await app.loop.run_in_executor(None, compare.diff, wti_client, project, base_string, translated_string)
    if diff and (diff.url_errors or diff.md_error):
        logger.info('errors found in string %s, project %s', translation['string_id'], translation['project_id'])
        user = await wti_client.user(translation['user_id'])
        if user.email is None:
            email = app[const.APP_SETTINGS].get('email.admin')
        else:
            email = user.email
        logger.info('Sending validation info to: %s', email)
        await mailer.send(app, email, diff)
        asyncio.ensure_future(app[const.STATS].increment('validations.failed'))
        if user.role != WtiUserRoles.manager:
            await wti_client.change_status(translated_string)
        return False
    else:
        asyncio.ensure_future(app[const.STATS].increment('validations.succeeded'))
        return True
