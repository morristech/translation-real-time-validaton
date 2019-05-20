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

EXCLUDED_LOCALES = ('ru', 'ar', 'he')
TRANSLATEABLE_SEG = (
    WtiTranslationStatus.untranslated,
    WtiTranslationStatus.unverified
)


async def get_locales_to_translate(wti_client, string_id, target_locales, target_segments):
    target_locales = [target_locale.lower() for target_locale in target_locales]
    coros = [wti_client.string(string_id, locale) for locale in target_locales]
    translations = await asyncio.gather(*coros)
    # if there is no translation for given locale
    existing_translations = list(filter(lambda d: isinstance(d, WtiString), translations))
    existing_locale = [trans.locale.lower() for trans in existing_translations]
    missing = [target_locale for target_locale in target_locales if target_locale not in existing_locale]
    # if translation is missing or unverified we should update it
    outdated = [d.locale for d in existing_translations if d and d.status in target_segments]
    missing.extend(outdated)
    return set(missing).difference(EXCLUDED_LOCALES)


async def machine_translate(dd_stats, wti_client, translate_client, data, target_segments=TRANSLATEABLE_SEG):
    html2text_conv = html2text.HTML2Text()
    html2text_conv.body_width = 0
    wti_translation = data['translation']
    project = await wti_client.get_project()
    string_id = wti_translation.get('string').get('id')
    logger.info('Auto translating, stringId: %s, for project: %s', string_id, project.get('name'))
    source_locale_code = project.get('source_locale').get('code')
    all_target_locale = project.get('target_locales', [])
    all_target_locale = [target_locale.get('code') for target_locale in all_target_locale]
    log_prefix = '[Project: %s][String: %s]' % (project.get('name'), string_id)
    target_locales = list(filter(lambda locale: locale != source_locale_code, all_target_locale))
    locales_to_update = await get_locales_to_translate(wti_client, string_id, target_locales, target_segments)
    text = wti_translation.get('text')
    if not text:
        logger.info('%s Skipping auto translation for empty source text', log_prefix)
        return
    asyncio.ensure_future(dd_stats.increment('translations', len(locales_to_update)))
    html_text = markdown.markdown(text)
    logger.info('%s Locales: %s will be translated', log_prefix, ','.join(locales_to_update))
    for target_locale_code in locales_to_update:
        sentry_tags = {
            'project': project.get('name'),
            'string_id': string_id,
            'target_locale': target_locale_code,
        }
        try:
            translated = await translate_client.translate(html_text, source_locale_code, target_locale_code,
                                                          'html')
            translated_md = html2text_conv.handle(translated.translatedText).lstrip('\n\n')
            await wti_client.update_translation(string_id, translated_md, target_locale_code,
                                                WtiTranslationStatus.unproofread, False)
            logger.info('%s Updated translation for locale %s ', log_prefix, target_locale_code)
            asyncio.ensure_future(dd_stats.increment('translations.succeeded'))
        except TranslationError:
            logger.exception('Could not machine translate text', extra=sentry_tags)
            asyncio.ensure_future(dd_stats.increment('translations.failed'))
        except UnsupportedLocale as ex:
            logger.error('%s', ex)
            asyncio.ensure_future(dd_stats.increment('translations.failed'))
        except WtiError:
            sentry_tags.update({'text': translated_md})
            logger.exception('Could not update translation', extra=sentry_tags)
            asyncio.ensure_future(dd_stats.increment('translations.failed'))
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
        locale_major = data['translation'].get('locale').lower()[0:2]
        should_machine_translate = locale_major == 'en' and machine_translation
        logger.info('Major locale: %s, machine translation enabled: %s', locale_major, should_machine_translate)
        if should_machine_translate:
            try:
                await machine_translate(app[const.STATS], wti_client, app[const.TRANSLATE_CLIENT], data)
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
