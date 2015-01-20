import logging
import asyncio
from aiohttp import web

from . import compare, translate, const

logger = logging.getLogger('notifier')


@asyncio.coroutine
def new_translation(req):
    data = yield from req.json()
    file_url = data['payload']['api_url']
    locale = req.app[const.MASTER_LOCALE]
    base = yield from translate.master(locale, file_url)
    other = data['payload']['translation']['text']
    diff = compare.diff(base, other)
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
