import logging
import logging.handlers
import asyncio
import json
import socket
from aiohttp import web, log

from . import const, tasks, worker

logger = logging.getLogger(__name__)


@asyncio.coroutine
def new_translation(req):
    data = yield from req.post()
    if 'payload' not in data:
        return web.HTTPBadRequest()
    payload = json.loads(data['payload'])
    translation = payload.get('translation')
    if translation is None or translation.get('status') != 'status_proofread':
        return web.Response()
    logger.info('translating url: %s, project_id: %s, user_id: %s' %
                (payload['api_url'], payload['project_id'], payload['user_id']))

    string_id = payload['string_id']
    wti_app = req.GET.get(const.REQ_APP_KEY)
    if not wti_app:
        logger.error('wti_app not in request query params')
        return web.HTTPBadRequest()
    wti_key = req.app[const.WTI_KEYS].get(wti_app)
    if not wti_key:
        logger.error('wti key for %s does not exist' % wti_app)
        return web.HTTPBadRequest()
    content_type = req.GET.get(const.REQ_TYPE_KEY, 'md')
    mailman_endpoint = req.app[const.MAILMAN]
    email_cms_host = req.app[const.EMAIL_CMS]
    req.app[const.ASYNC_WORKER].start(
        tasks.compare_with_master, wti_key, mailman_endpoint, string_id, payload, content_type, email_cms_host)
    return web.Response()


@asyncio.coroutine
def project(req):
    api_key = req.match_info['api_key']
    params = yield from req.post()
    user_email = params['email']
    mailman_endpoint = req.app[const.MAILMAN]

    req.app[const.ASYNC_WORKER].start(tasks.validate_project, api_key, mailman_endpoint, user_email)

    return web.Response()


@asyncio.coroutine
def healthcheck(req):
    return web.Response()


def app(global_config, **settings):
    logger.info('Loading configuration')
    loop = asyncio.get_event_loop()
    loop.set_debug(False)

    app = web.Application(logger=logger, loop=loop)
    app[const.ASYNC_WORKER] = worker.Worker(loop)

    wti_keys = settings.get('wti_keys')
    if not wti_keys:
        raise ValueError('wti keys are missing')
    app[const.WTI_KEYS] = dict(map(lambda i: i.split(':'), filter(bool, wti_keys.split('\n'))))
    mandrill_key = settings.get('mandrill')
    if not mandrill_key:
        raise ValueError('mandrill key is missing')
    app[const.MANDRILL_KEY] = mandrill_key
    app[const.EMAIL_CMS] = settings.get('email_cms')
    app[const.MAILMAN] = settings['mailman_endpoint_url']

    logger.info('Initializing public api endpoints')
    app.router.add_route('GET', '/healthcheck', healthcheck)
    app.router.add_route('POST', '/projects/{api_key}', project)
    app.router.add_route('POST', '/translations', new_translation)

    return app
