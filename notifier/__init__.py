import logging
import logging.handlers
import asyncio
import json
from aiohttp import web

from . import const, tasks, worker, sendgrid

logger = logging.getLogger(__name__)


@asyncio.coroutine
def new_translation(req):
    """
    @api {POST} /translations/?wti_apikey={}&type={} Validate translation
    @apiGroup Webhooks
    @apiDescription WTI webhook endpoint. Schedule translation validation task.
    @apiParam (Query String) {string} wti_apikey
    @apiParam (Query String) {string="ios","java","md"} [type=md]
    @apiParam (Request Body) {string} payload WTI payload

    @apiError 400 Missing `wti_key` or `payload`
    """
    email_provider = req.app[const.EMAIL_PROVIDER]
    data = yield from req.post()
    content_type = req.GET.get(const.REQ_TYPE_KEY, 'md')
    wti_key = req.GET.get(const.REQ_APP_KEY)

    if not wti_key:
        logger.error('wti_key not in request query params ')
        return web.HTTPBadRequest()
    if 'payload' not in data:
        return web.HTTPBadRequest()

    payload = json.loads(data['payload'])
    try:
        if isinstance(payload, list):
            translations = [p for p in payload]
        else:
            translations = [payload]
    except AttributeError:
        logger.exception('got unexpected data %s', payload)
        return web.Response()

    for translation in translations:
        logger.info('translating project_id: %s, user_id: %s',
                    translation['project_id'], translation['user_id'])
        req.app[const.ASYNC_WORKER].start(
            tasks.validate_translation, wti_key, email_provider, translation, content_type)
    return web.Response()


@asyncio.coroutine
def project(req):
    """
    @api {POST} /projects/{api_key} Validate
    @apiGroup Projects
    @apiDescription Schedule project validation and notify via provided email.
    @apiParam (Query String) {string} wti_apikey
    @apiParam (Query String) {string="ios","java","md"} [type=md]
    @apiParam (POST) {string} email email to notify
    """
    email_provider = req.app[const.EMAIL_PROVIDER]
    params = yield from req.post()
    user_email = params['email']
    content_type = req.GET.get(const.REQ_TYPE_KEY, 'md')
    wti_key = req.match_info['api_key']
    if not wti_key:
        logger.error('wti_key not in request query params ')
        return web.HTTPBadRequest()

    req.app[const.ASYNC_WORKER].start(
        tasks.validate_project, wti_key, email_provider, user_email, content_type)

    return web.Response()


@asyncio.coroutine
def healthcheck(req):
    """
    @api {GET} /healthcheck Healthcheck
    @apiGroup Healthcheck
    """
    return web.Response()


def app(global_config, **settings):
    logger.info('Loading configuration')
    loop = asyncio.get_event_loop()
    loop.set_debug(False)

    app = web.Application(logger=logger, loop=loop)
    app[const.ASYNC_WORKER] = worker.Worker(loop)
    app[const.EMAIL_PROVIDER] = sendgrid.SendgridProvider(
        settings['sendgrid.user'],
        settings['sendgrid.password'],
        settings['from.email'],
        settings['from.name'],
        loop=loop
    )

    logger.info('Initializing public api endpoints')
    app.router.add_route('GET', '/healthcheck', healthcheck)
    app.router.add_route('POST', '/projects/{api_key}', project)
    app.router.add_route('POST', '/translations', new_translation)

    return app
