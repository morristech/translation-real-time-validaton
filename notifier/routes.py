import asyncio
import json
import logging

from aiohttp import web

from . import const, wti, validator, sync
from .model import *

logger = logging.getLogger(__name__)


async def healthcheck(req):
    """
    @api {GET} /healthcheck Healthcheck
    @apiGroup Healthcheck
    """
    return web.Response()


def _list_projects(settings):
    projects = settings.get('projects', '')
    result = {}
    projects = projects.split('\n')
    for project in projects:
        bits = project.split(':')
        if len(bits) > 1:
            result[bits[0].strip()] = bits[1].strip()
    return result


async def new_translation(req):
    """
    @api {POST} /translations/?wti_apikey={}&type={} Validate translation
    @apiGroup Webhooks
    @apiDescription WTI webhook endpoint. Schedule translation validation task.
    @apiParam {string} project project name, allows to match wti key from app settings
    @apiParam {string} wti_apikey
    @apiParam {string} type *OPTIONAL* Default: `md`. Supported: `md`, `ios`, `java`.
    @apiParam {string} callback_url *OPTIONAL* when validation finishes, callback request can be send
    @apiParam (Request JSON) {string} payload WTI payload

    @apiError 400 Missing `wti_key` or `payload`
    """
    try:
        data = await req.json()
        logger.info('Payload %s', data)
    except json.decoder.JSONDecodeError:
        return web.HTTPBadRequest(reason='malformed body, expected json')

    wti_key = req.query.get(const.REQ_APP_KEY)
    if not wti_key:
        project_name = req.query.get(const.REQ_PROJECT)
        projects = _list_projects(req.app[const.APP_SETTINGS])
        wti_key = projects.get(project_name)
        if not wti_key:
            msg = 'no wti_key or valid project in request query params'
            logger.error(msg)
            return web.HTTPBadRequest(reason=msg)

    content_type = req.query.get(const.REQ_TYPE_KEY, 'md')
    if content_type not in WtiContentTypes.__members__:
        msg = 'content_type %s not valid' % content_type
        logger.error(msg)
        return web.HTTPBadRequest(reason=msg)
    content_type = WtiContentTypes[content_type]

    if 'payload' not in data:
        logger.error('payload not in request data')
        return web.HTTPBadRequest(reason='payload not in request data')

    payload = data['payload']
    payload = payload if isinstance(payload, list) else [payload]
    wti_client = wti.WtiClient(wti_key)
    callback_url = req.query.get(const.REQ_CALLBACK_KEY)
    await asyncio.shield(validator.check_translations(req.app, wti_client, content_type, payload,
                                                      callback_url=callback_url))

    req.app[const.STATS].increment('validation.count')
    return web.Response()


async def zendesk_sync(req):
    await asyncio.shield(sync.sync_zendesk(req.app))
    return web.Response()


def init(router):
    logger.info('Initializing public api endpoints')

    router.add_route('GET', '/healthcheck', healthcheck)
    router.add_route('POST', '/translations', new_translation)
    # router.add_route('POST', '/zendesk/sync', zendesk_sync)
