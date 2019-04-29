import asyncio
import logging

from aiohttp import web

from . import const

IGNORED_PATHS = ['healthcheck']

logger = logging.getLogger(__name__)


def log_response_status(res, req):
    status = getattr(res, 'status', 500)
    if status > 299:
        msg = 'operation not successful status:%s path:%s query_string:%s'
        logger.warning(msg, res.status, req.raw_path, req.query_string)


def send_stats(res, req):
    stats_client = req.app[const.STATS]
    path = req.raw_path.strip('/').replace('/', '.')
    if path in IGNORED_PATHS:
        return
    status = getattr(res, 'status', 'undefined')
    tags = {
        'status': status,
        'path': path
    }
    asyncio.ensure_future(stats_client.increment('requests', tags=tags))


@web.middleware
async def status_logging_middleware(req, handler):
    try:
        res = await handler(req)
        if res:
            log_response_status(res, req)
        return res
    except web.HTTPException as res_ex:
        log_response_status(res_ex, req)
        raise
    except Exception:
        logger.exception("Request %s failed", req)
        return web.HTTPInternalServerError()


@web.middleware
async def stats_middleware(req, handler):
    try:
        res = await handler(req)
        send_stats(res, req)
        return res
    except web.HTTPException as res_ex:
        send_stats(res_ex, req)
        raise
