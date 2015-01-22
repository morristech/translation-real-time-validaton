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

    if payload['translation']['status'] != 'status_unproofread':
        return web.Response()

    string_id = payload['string_id']
    locale = req.app[const.MASTER_LOCALE]
    wti_key = req.app[const.WTI_KEY]
    mandrill_key = req.app[const.MANDRILL_KEY]

    base = yield from translate.string(wti_key, locale, string_id)
    other = payload['translation']['text']
    diff = yield from compare.diff(base, other)

    if diff:
        diff.base_path = 'Language: {}'.format(locale)
        diff.other_path = 'Language: {}'.format(payload['locale'])
        user_id = payload['user_id']
        user = yield from translate.user(wti_key, user_id)
        user_email = user.get('email', 'tomek.kwiecien@gmail.com')
        yield from mailer.send(mandrill_key, user_email, diff)
        yield from translate.change_status(wti_key, payload['locale'], string_id, other)

    return web.Response()


@asyncio.coroutine
def all_translations(req):
    api_key = req.GET['project_key']
    locales, master_files, _ = yield from translate.files(api_key)
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
    app.router.add_route('GET', '/', healthcheck)
    app.router.add_route('GET', '/translations', all_translations)
    app.router.add_route('POST', '/translations', new_translation)

    return app
