import asyncio
import logging
from collections import namedtuple
from functools import partial

from . import translate, compare, mailer

PROJECT_URL = 'https://webtranslateit.com/api/projects/{}.json'
SECTION_URL = 'https://webtranslateit.com/en/projects/{project_id}-{project_name}/locales/\
{master_locale}..{other_locale}/strings/{string_id}'


DiffError = namedtuple('DiffError', ['base', 'other', 'diff', 'section_link', 'file_path', 'base_path', 'other_path'])
UrlError = namedtuple('UrlError', ['url', 'status_code', 'section_link', 'file_path', 'locale'])
logger = logging.getLogger(__name__)


def _make_url_error(base, other, file_path, master_locale, other_locale, section_link, url_diff):
    locale = master_locale if url_diff.files == base else other_locale
    return UrlError(
        url=url_diff.url,
        status_code=url_diff.status_code,
        section_link=section_link,
        file_path=file_path,
        locale=locale
    )


def filter_filename(files, file_id):
    filtered_files = list(filter(lambda f: f['id'] == file_id, files))
    if not filtered_files:
        logger.error('No file could be found for id {} in project files {}'.format(file_id, files))
        return ''
    return filtered_files[0].get('name')


@asyncio.coroutine
def compare_with_master(wti_key, mailman_client, string_id, payload, content_type, email_cms_host):
    # TODO refactor
    project = yield from translate.project(wti_key)
    if not project:
        return
    master_locale = project.locales.source
    other_locale = payload['locale']
    base_string = yield from translate.string(wti_key, master_locale, string_id)
    base = base_string.text
    other = payload['translation']['text']
    filename = filter_filename(project.files, payload['file_id'])
    section_link = SECTION_URL.format(project_id=project.id, project_name=project.name,
                                      master_locale=master_locale, other_locale=other_locale,
                                      string_id=payload['string_id']),
    user_id = payload['user_id']
    user = yield from translate.user(wti_key, user_id)
    user_email = user.get('email')
    topic = 'Translations not passing the validation test - file {}, language {}, string_id {}'.format(filename,
                                                                                                       other_locale,
                                                                                                       string_id)

    if content_type == 'ios' and filename[-4:] == '.txt':
        url_diffs = compare.urls(base, other)
        url_errors = list(map(partial(_make_url_error, base, other, filename, master_locale, other_locale, section_link),
                              url_diffs))
        logger.info(topic)
        result = yield from mailer.send(mailman_client, user_email, [], url_errors, content_type, topic)
        if result:
            logger.info('sending email to agent %s', user_id)
        else:
            logger.error('unable to notify agent %s', user_id)

    elif filename[-8:] == '.strings':
        return
    else:
        diff = yield from compare.diff(base, other, content_type)
        if diff:
            error = DiffError(
                base=base,
                other=other,
                diff=diff[0],
                section_link=section_link,
                file_path='File: {}'.format(filename),
                base_path='Language: {}'.format(master_locale),
                other_path='Language: {}'.format(other_locale)
            )
            logger.info(topic)
            if user.get('role') != 'manager':
                yield from translate.change_status(wti_key, payload['locale'], string_id, other)
            result = yield from mailer.send(mailman_client, user_email, [error], [], content_type, topic)
            if result:
                logger.info('sending email to agent %s', user_id)
            else:
                logger.error('unable to notify agent %s', user_id)
        else:
            # yield from aiohttp.request('PUT', email_cms_host)
            pass


@asyncio.coroutine
def validate_project(wti_key, mailman_client, user_email):
    project = yield from translate.project(wti_key)
    locales = project.locales
    strings = yield from translate.strings(wti_key)
    errors = []
    for string in strings:
        base = yield from translate.string(wti_key, locales.source, string.id)
        for locale in locales.targets:
            translation = yield from translate.string(wti_key, locale, string.id)
            error = yield from compare.diff(base.text, translation.text)
            if error:
                errors.append(error)
    yield from mailer.send(mailman_client, user_email, errors, [])
