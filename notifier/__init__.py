import logging
import asyncio
from aiohttp import web

from . import const, mailer, wti, zendesk, routes, notifier

logger = logging.getLogger(__name__)


def app(global_config, **settings):
    logger.info('Loading configuration')
    loop = asyncio.get_event_loop()
    loop.set_debug(False)

    app = web.Application(logger=logger, loop=loop)
    app[const.APP_SETTINGS] = settings
    app[const.EMAIL_PROVIDER] = mailer.SendgridProvider(settings)
    app[const.WTI_DYNAMIC_CONTENT] = wti.WtiClient(settings['wti.api_key'])
    app[const.ZENDESK_DC] = zendesk.ZendeskDynamicContent(settings)
    app[const.SLACK_NOTIFIER] = notifier.SlackNotifier(settings)

    routes.init(app.router)

    return app
