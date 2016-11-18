import logging

from . import compare, mailer
from .model import *

logger = logging.getLogger(__name__)
UPDATE_PATH = 'admin/refresh_wti'


async def check_translations(app, wti_client, content_type, payload):
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
    if diff:
        user = await wti_client.user(translation['user_id'])
        await mailer.send(app, user.email, diff)
        if user.role != WtiUserRoles.manager:
            await wti.change_status(translated_string)


async def validate_project(wti_key, mail_client, user_email):
    pass