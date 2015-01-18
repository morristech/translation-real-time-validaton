import logging
import asyncio
from aiohttp import web

logger = logging.getLogger('notifier')


@asyncio.coroutine
def healthcheck(req):
    return web.Response()


def main(global_config, **settings):
    logger.info('Loading configuration')
    loop = asyncio.get_event_loop()
    loop.set_debug(False)

    app = web.Application(logger=logger, loop=loop)

    logger.info('Initializing public api endpoints')
    app.router.add_route('GET', '/', healthcheck)

    return app
