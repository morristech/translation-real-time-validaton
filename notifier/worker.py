import asyncio
import aiohttp

from . import const


class Worker(object):
    def __init__(self, loop):
        self.loop = loop
        # self.app = aiohttp.web.Application()
        # self.app[const.TASK_QUEUE] = []

    def start(self, task, *args):
        asyncio.async(task(*args))
