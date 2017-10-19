import logging

from . import compare, mailer, const
from .model import *

logger = logging.getLogger(__name__)
UPDATE_PATH = 'admin/refresh_wti'


async def check_translations(app, wti_client, content_type, payload):
    logger.info('translating %s segments', len(payload))
    for data in payload:
        if data['translation'].get('status') != WtiTranslationStatus.proofread.value:
            continue
        logger.debug('translating %s', data)
        await _check_translation(app, wti_client, content_type, data)


async def _check_translation(app, wti_client, content_type, translation):
    project = await wti_client.project(translation['file_id'], content_type)
    base_string = await wti_client.string(translation['string_id'], project.master_locale)
    translated_string = WtiString(translation['string_id'], translation['locale'], translation['translation']['text'])
    diff = await app.loop.run_in_executor(None, compare.diff, wti_client, project, base_string, translated_string)
    if diff and (diff.url_errors or diff.md_error):
        logger.info('errors found in string %s, project %s', translation['string_id'], translation['project_id'])
        user = await wti_client.user(translation['user_id'])
        await mailer.send(app, user.email, diff)
        app[const.STATS].increment('validation.failed')
        if user.role != WtiUserRoles.manager:
            await wti_client.change_status(translated_string)
    else:
        app[const.STATS].increment('validation.success')

