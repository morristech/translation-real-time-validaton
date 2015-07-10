import logging
import logging.handlers
import asyncio
import json
from aiohttp import web, log

from . import const, tasks, worker

logger = log.web_logger
logger.setLevel(logging.INFO)


@asyncio.coroutine
def new_translation(req):
    data = yield from req.post()
    if 'payload' not in data:
        return web.HTTPBadRequest()
    payload = json.loads(data['payload'])
    translation = payload.get('translation')
    if translation == None or translation.get('status') != 'status_proofread':
        return web.Response()
    logger.info('translating url: %s, project_id: %s, user_id: %s' %
                (payload['api_url'], payload['project_id'], payload['user_id']))

    string_id = payload['string_id']
    wti_app = req.GET[const.REQ_APP_KEY]
    wti_key = req.app[const.WTI_KEYS].get(wti_app)
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

    wti_keys = settings.get('wti_keys')
    if not wti_keys:
        raise ValueError('wti keys are missing')
    app[const.WTI_KEYS] = wti_keys
    mandrill_key = settings.get('mandrill')
    if not mandrill_key:
        raise ValueError('mandrill key is missing')
    app[const.MANDRILL_KEY] = mandrill_key

    logger.info('Initializing public api endpoints')
    app.router.add_route('GET', '/healthcheck', healthcheck)
    app.router.add_route('POST', '/projects/{api_key}', project)
    app.router.add_route('POST', '/translations', new_translation)

    return app
