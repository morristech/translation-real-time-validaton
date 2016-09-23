import asyncio
import logging

from .segment import build_segment, build_segment_from_payload
from . import mailer, wti, validators

TRANSLATION_EMAIL_TOPIC = 'Translations not passing the validation test - file {}, language {}, string_id {}'
PROJECT_EMAIL_TOPIC = 'Project not passing the validation test - {}'

logger = logging.getLogger(__name__)


@asyncio.coroutine
def validate_translation(wti_key, mail_client, translation_payload, content_type):
    segment = yield from build_segment_from_payload(wti_key, translation_payload, content_type)
    validator = validators.dispatch(segment)
    if not validator:
        logger.error('No validator found for segment:\n%s\nPayload:\n%s', segment, translation_payload)
        return

    valid = yield from validator(segment).validate()
    if not valid:
        if validator.notify_agent:
            topic = TRANSLATION_EMAIL_TOPIC.format(segment.filename, segment.locale, segment.string_id)
            logger.info(topic)
            result = yield from mailer.send(mail_client, segment.user_email,
                                            [segment], segment.content_type, topic)
            if result:
                logger.info('sending email to agent %s', segment.user_id)
            else:
                logger.error('unable to notify agent %s', segment.user_id)

        if validator.change_status:
            if segment.user_role != 'manager':
                yield from wti.change_status(wti_key, segment.locale, segment.string_id, segment.content)


@asyncio.coroutine
def validate_project(wti_key, mail_client, user_email, content_type='md'):
    project = yield from wti.project(wti_key)
    locales = project.locales
    strings = yield from wti.strings(wti_key)
    invalid_segments = []
    for string in strings:
        base = yield from wti.string(wti_key, locales.source, string.id)
        for locale in locales.targets:
            translation = yield from wti.string(wti_key, locale, string.id)
            segment = build_segment(project, string, base, translation)
            validator = validators.dispatch(segment)
            if not validator:
                logger.error('No validator found during validating project %s (%s), segment:\n%s',
                             project.name, segment)
                return
            valid = yield from validator(segment).validate()
            if not valid:
                invalid_segments.append(segment)
    topic = PROJECT_EMAIL_TOPIC.format(project.name)
    yield from mailer.send(mail_client, user_email, invalid_segments, content_type, topic)
