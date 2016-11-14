import logging
import json
import asyncio
from aiohttp import web

from . import const, wti, validator
from .model import *

logger = logging.getLogger(__name__)


async def healthcheck(req):
    """
    @api {GET} /healthcheck Healthcheck
    @apiGroup Healthcheck
    """
    return web.Response()


async def new_translation(req):
    """
    @api {POST} /translations/?wti_apikey={}&type={} Validate translation
    @apiGroup Webhooks
    @apiDescription WTI webhook endpoint. Schedule translation validation task.
    @apiParam {string} wti_apikey
    @apiParam {string} type *OPTIONAL* Default: `md`. Supported: `md`, `ios`, `java`.
    @apiParam (Request JSON) {string} payload WTI payload

    @apiError 400 Missing `wti_key` or `payload`
    """
    wti_key = req.GET.get(const.REQ_APP_KEY)
    if not wti_key:
        msg = 'wti_key not in request query params'
        logger.error(msg)
        return web.HTTPBadRequest(reason=msg)

    content_type = req.GET.get(const.REQ_TYPE_KEY, 'md')
    if content_type not in WtiContentTypes.__members__:
        msg = 'content_type %s not valid' % content_type
        logger.error(msg)
        return web.HTTPBadRequest(reason=msg)
    content_type = WtiContentTypes[content_type]

    data = await req.post()
    if 'payload' not in data:
        logger.error('payload not in request data')
        return web.HTTPBadRequest(reason='payload not in request data')

    payload = json.loads(data['payload'])
    payload = payload if isinstance(payload, list) else [payload]
    wti_client = wti.WtiClient(wti_key)
    asyncio.ensure_future(validator.check_translations(req.app, wti_client, content_type, payload))

    return web.Response()


async def project(req):
    """
    @api {POST} /projects/{api_key} Validate
    @apiGroup Projects
    @apiDescription Schedule project validation and notify via provided email.
    @apiParam {string} api_key
    @apiParam (POST Parameters) {string} email email to notify
    """
    # api_key = req.match_info['api_key']
    # params = yield from req.post()
    # user_email = params['email']

    # req.app[const.ASYNC_WORKER].start(
    #     tasks.validate_project, api_key, mailman_endpoint, user_email)

    return web.Response()


def init(router):
    logger.info('Initializing public api endpoints')

    router.add_route('GET', '/healthcheck', healthcheck)
    router.add_route('POST', '/translations', new_translation)
