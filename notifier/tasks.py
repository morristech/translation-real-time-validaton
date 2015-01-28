import asyncio

from . import translate, compare, mailer


@asyncio.coroutine
def compare_with_master(wti_key, locale, string_id, mandrill_key, payload):
    base_string = yield from translate.string(wti_key, locale, string_id)
    base = base_string.text
    other = payload['translation']['text']
    error = yield from compare.diff(base, other)

    #TODO refactor
    if error:
        error.file_path = 'File: {} Segment: {}'.format('TODO here', 'and here')
        error.base_path = 'Language: {}'.format(locale)
        error.other_path = 'Language: {}'.format(payload['locale'])
        user_id = payload['user_id']
        user = yield from translate.user(wti_key, user_id)
        user_email = user.get('email')
        mail_res = yield from mailer.send(mandrill_key, user_email, [error])
        status_res = yield from translate.change_status(wti_key, payload['locale'], string_id, other)


@asyncio.coroutine
def validate_project(api_key, mandrill_key):
    locales = yield from translate.locales(api_key)
    strings = yield from translate.strings(api_key)
    errors = []
    for string in strings:
        base = yield from translate.string(api_key, locales.source, string.id)
        for locale in locales.targets:
            translation = yield from translate.string(api_key, locale, string.id)
            error = yield from compare.diff(base.text, translation.text)
            if error:
                errors.append(error)
    yield from mailer.send(mandrill_key, user_email, errors)
