import logging
import asyncio
from aiohttp import web

from . import const, mailer, wti, zendesk, routes, notifier, stats

logger = logging.getLogger(__name__)


async def stop_http_clients(app):
    await app[const.ZENDESK_DC].shutdown()
    await app[const.SLACK_NOTIFIER].shutdown()


async def start_http_clients(app):
    await app[const.ZENDESK_DC].bootstrap()
    await app[const.SLACK_NOTIFIER].bootstrap()


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
    app[const.STATS] = stats.Stats(settings['datadog_api_key'])

    routes.init(app.router)
    app.on_startup.append(start_http_clients)
    app.on_cleanup.append(stop_http_clients)

    return app
