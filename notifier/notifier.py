import logging
import json
from functools import partial

import aiohttp

from . import httpclient

logger = logging.getLogger(__name__)


class SlackNotifier:
    SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/%s'

    def __init__(self, settings):
        self._client = httpclient.HttpClient(self.SLACK_WEBHOOK_URL)
        self._notify = partial(self._client.post, settings['slack.token'])
        self._slack_username = settings['slack.username']

    async def bootstrap(self):
        await self._client.bootstrap()

    async def shutdown(self):
        await self._client.close()

    async def notify(self, keys):
        message = 'translations updated for following keys: %s' % keys
        payload = {'username': self._slack_username, 'text': message}
        try:
            await self._notify(data=json.dumps(payload))
        except aiohttp.ClientResponseError as ex:
            msg = 'unable to post notification in slack status: %s, message: %s, request info: %s'
            logger.error(msg, ex.status, ex.message, ex.request_info)
