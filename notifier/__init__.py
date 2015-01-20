import logging
import asyncio
from aiohttp import web

from . import compare, translate, const, mailer

logger = logging.getLogger('notifier')


@asyncio.coroutine
def new_translation(req):
    data = yield from req.json()
    payload = data['payload']
    file_url = payload['api_url']
    locale = req.app[const.MASTER_LOCALE]
    wti_key = req.app[const.WTI_KEY]
    mandrill_key = req.app[const.MANDRILL_KEY]

    base = yield from translate.master(wti_key, locale, file_url)
    other = payload['translation']['text']
    diff = yield from compare.diff(base + '\n\naaa', other)
    diff.base_path = 'aaa'
    diff.other_path = 'bbb'

    if diff:
        user_id = payload['user_id']
        user = yield from translate.user(wti_key, user_id)
        mailer.send(mandrill_key, user, diff)

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
    app.router.add_route('POST', '/translations', new_translation)

    return app
