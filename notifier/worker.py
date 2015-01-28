import asyncio
import aiohttp
import logging

from . import const

logger = logging.getLogger('notifier')


class Worker(object):

    def __init__(self, loop):
        self.loop = loop

    def start(self, task, *args):
        task = asyncio.async(task(*args))
