import logging
import asyncio
from aiohttp import web

from . import compare, translate, const

logger = logging.getLogger('notifier')


@asyncio.coroutine
def new_translation(req):
    data = yield from req.json()
    payload = data['payload']
    file_url = payload['api_url']
    locale = req.app[const.MASTER_LOCALE]
    wti_key = translate.get_wti_key(file_url)

    base = yield from translate.master(wti_key, locale, file_url)
    other = payload['translation']['text']
    diff = yield from compare.diff(base, other)

    if diff:
        user_id = payload['user_id']
        user = yield from translate.user(wti_key, user_id)
        mailer.send(user, diff)

    return web.Response()


@asyncio.coroutine
def healthcheck(req):
    return web.Response()


def main(global_config, **settings):
    logger.info('Loading configuration')
    loop = asyncio.get_event_loop()
    loop.set_debug(False)

    app = web.Application(logger=logger, loop=loop)

    master_locale = settings.get('srv.locale', 'en')
    app[const.MASTER_LOCALE] = master_locale

    logger.info('Initializing public api endpoints')
    app.router.add_route('GET', '/', healthcheck)
    app.router.add_route('POST', '/translations', new_translation)

    return app
