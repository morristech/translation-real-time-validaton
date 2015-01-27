import logging
import asyncio
import json
from aiohttp import web

from . import const, tasks, worker

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

    req.app.worker.start(tasks.compare_with_master, wti_key, locale, string_id, mandrill_key, payload)
    return web.Response()


@asyncio.coroutine
def project(req):
    api_key = req.match_info['api_key']
    mandrill_key = req.app[const.MANDRILL_KEY]
    req.app.worker.start(tasks.validate_project, api_key, mandrill_key)
    return web.Response()


@asyncio.coroutine
def healthcheck(req):
    return web.Response()


def main(global_config, **settings):
    logger.info('Loading configuration')
    loop = asyncio.get_event_loop()
    loop.set_debug(False)

    app = web.Application(logger=logger, loop=loop)
    app.worker = worker.Worker(loop)

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
