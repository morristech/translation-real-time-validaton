import logging
import asyncio
import json
from aiohttp import web

from . import compare, translate, const, mailer

logger = logging.getLogger('notifier')


@asyncio.coroutine
def new_translation(req):
    data = yield from req.post()
    payload = json.loads(data['payload'])
    print('got req with status {}'.format(payload['translation']['status']))
    if payload['translation']['status'] != 'status_unproofread':
        return web.Response()

    string_id = payload['string_id']
    locale = req.app[const.MASTER_LOCALE]
    wti_key = req.app[const.WTI_KEY]
    mandrill_key = req.app[const.MANDRILL_KEY]

    base_string = yield from translate.string(wti_key, locale, string_id)
    base = base_string.text
    other = payload['translation']['text']
    error = yield from compare.diff(base, other)

    if error:
        error.file_path = 'File: {} Segment: {}'.format('TODO here', 'and here')
        error.base_path = 'Language: {}'.format(locale)
        error.other_path = 'Language: {}'.format(payload['locale'])
        user_id = payload['user_id']
        user = yield from translate.user(wti_key, user_id)
        #TODO get email from users
        user_email = user.get('email', 'tomek.kwiecien@gmail.com')
        mail_res = yield from mailer.send(mandrill_key, user_email, [error])
        status_res = yield from translate.change_status(wti_key, payload['locale'], string_id, other)
    else:
        print('no errors comparing:\n\n{}\n\n{}\n'.format(base, other))

    return web.Response()


@asyncio.coroutine
def project(req):
    api_key = req.match_info['api_key']
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
    return web.Response()


@asyncio.coroutine
def healthcheck(req):
    return web.Response()


def main(global_config, **settings):
    logger.info('Loading configuration')
    loop = asyncio.get_event_loop()
    loop.set_debug(False)

    app = web.Application(logger=logger, loop=loop)

    master_locale = settings.get('srv.locale', 'en-US')
    app[const.MASTER_LOCALE] = master_locale
    wti_key = settings.get('srv.wti', 'EIEThAR3Dt_JQCOyMa4awA')
    app[const.WTI_KEY] = wti_key
    mandrill_key = settings.get('srv.mandrill', 'HW5VKp-p1Gk7GV12iwrwNQ')
    app[const.MANDRILL_KEY] = mandrill_key

    logger.info('Initializing public api endpoints')
    app.router.add_route('GET', '/healthcheck', healthcheck)
    app.router.add_route('GET', '/projects/{api_key}', project)
    app.router.add_route('POST', '/translations', new_translation)

    return app
