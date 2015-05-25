import logging
import logging.handlers
import asyncio
import json
from aiohttp import web

from . import const, tasks, worker

logger = logging.getLogger('notifier')
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('asyncio').setLevel(logging.ERROR)
hlr = logging.handlers.RotatingFileHandler('var/log/translation-validator.log', maxBytes=10000000)
logger.addHandler(hlr)
accessHlr = logging.handlers.RotatingFileHandler('var/log/translation-validator_access.log', maxBytes=10000000)
logging.getLogger('aiohttp').addHandler(accessHlr)


@asyncio.coroutine
def new_translation(req):
    data = yield from req.post()
    payload = json.loads(data['payload'])
    if payload['translation']['status'] != 'status_proofread':
        return web.Response()

    string_id = payload['string_id']
    wti_key = req.app[const.WTI_KEY]
    mandrill_key = req.app[const.MANDRILL_KEY]
    req.app[const.ASYNC_WORKER].start(tasks.compare_with_master, wti_key, mandrill_key, string_id, payload)
    return web.Response()


@asyncio.coroutine
def project(req):
    api_key = req.match_info['api_key']
    params = yield from req.post()
    user_email = params['email']
    mandrill_key = req.app[const.MANDRILL_KEY]

    req.app[const.ASYNC_WORKER].start(tasks.validate_project, api_key, mandrill_key, user_email)

    return web.Response()


@asyncio.coroutine
def healthcheck(req):
    return web.Response()


def main(global_config, **settings):
    logger.info('Loading configuration')
    loop = asyncio.get_event_loop()
    loop.set_debug(False)

    app = web.Application(logger=logger, loop=loop)
    app[const.ASYNC_WORKER] = worker.Worker(loop)

    wti_key = settings.get('wti')
    if wti_key == None:
        raise ValueError('wti key is missing')
    app[const.WTI_KEY] = wti_key
    mandrill_key = settings.get('mandrill')
    if wti_key == None:
        raise ValueError('mandrill key is missing')
    app[const.MANDRILL_KEY] = mandrill_key

    logger.info('Initializing public api endpoints')
    app.router.add_route('GET', '/healthcheck', healthcheck)
    app.router.add_route('POST', '/projects/{api_key}', project)
    app.router.add_route('POST', '/translations', new_translation)

    return app
