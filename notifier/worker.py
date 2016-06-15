import asyncio
import logging

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
        asyncio.async(handle_exception(task, args))
