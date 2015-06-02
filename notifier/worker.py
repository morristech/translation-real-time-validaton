import asyncio
from aiohttp import log

from . import const

logger = log.web_logger


@asyncio.coroutine
def handle_exception(task, args):
    try:
        result = yield from task(*args)
        return result
    except Exception:
        logger.exception()


class Worker(object):

    def __init__(self, loop):
        self.loop = loop

    def start(self, task, *args):
        result = asyncio.async(handle_exception(args))
