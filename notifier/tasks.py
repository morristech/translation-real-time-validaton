import asyncio
import aiohttp
import logging

from . import translate, compare, mailer


PROJECT_URL = 'https://webtranslateit.com/api/projects/{}.json'


def filter_filename(files, file_id):
    filtered_files = list(filter(lambda f: f['id'] == file_id, files))
    if not filtered_files:
        logging.error('No file could be found for id {} in project files {}'.format(file_id, files))
        return ''
    return filtered_files[0].get('name')


@asyncio.coroutine
def compare_with_master(wti_key, string_id, mandrill_key, payload):
    #TODO refactor
    project = yield from translate.project(wti_key)
    master_locale = project.locales.source
    base_string = yield from translate.string(wti_key, master_locale, string_id)
    base = base_string.text
    other = payload['translation']['text']
    error = yield from compare.diff(base, other)
    if error:
        filename = filter_filename(project.files, payload['file_id'])
        error.file_path = 'File: {}'.format(filename)
        error.base_path = 'Language: {}'.format(master_locale)
        error.other_path = 'Language: {}'.format(payload['locale'])
        user_id = payload['user_id']
        user = yield from translate.user(wti_key, user_id)
        user_email = user.get('email')
        mail_res = yield from mailer.send(mandrill_key, user_email, [error])
        status_res = yield from translate.change_status(wti_key, payload['locale'], string_id, other)


@asyncio.coroutine
def validate_project(wti_key, mandrill_key, user_email):
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
    yield from mailer.send(mandrill_key, user_email, errors)
