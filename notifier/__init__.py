import logging
import asyncio
from aiohttp import web

from . import const, mailer, routes

logger = logging.getLogger(__name__)


def app(global_config, **settings):
    logger.info('Loading configuration')
    loop = asyncio.get_event_loop()
    loop.set_debug(False)

    app = web.Application(logger=logger, loop=loop)
    app[const.SETTINGS] = settings
    app[const.EMAIL_PROVIDER] = mailer.SendgridProvider(settings)
    routes.init(app.router)

    return app
