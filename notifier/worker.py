import asyncio
from aiohttp import log

from . import const

logger = logging.getLogger(__name__)


@asyncio.coroutine
def handle_exception(task, args):
    try:
        result = yield from task(*args)
        return result
    except Exception:
        logger.exception('there was an error while handling request')


class Worker(object):

    def __init__(self, loop):
        self.loop = loop

    def start(self, task, *args):
        result = asyncio.async(handle_exception(task, args))
