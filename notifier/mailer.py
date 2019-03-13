import logging
import os
import aiohttp
import simplejson as json
from time import time
from functools import lru_cache
from pybars import Compiler
import inlinestyler.utils as inline_styler

from . import const

logger = logging.getLogger(__name__)


@lru_cache()
def _read_template_file(filename):
    path = os.path.join('./notifier/templates', filename)
    with open(path, 'r') as fp:
        return fp.read()


def _create_template(diff):
    diff = diff._asdict()
    template_source = _read_template_file('diff_email.hbs')
    diff['css'] = _read_template_file('basic.css')
    template = Compiler().compile(template_source)(diff)
    email_body = inline_styler.inline_css(template)
    return email_body


async def _send_template(app, email, template):
    client = app[const.EMAIL_PROVIDER]
    await client.send(email, template)


async def send(app, email, diff):
    template = _create_template(diff)
    await _send_template(app, email, template)


class SendgridProvider:

    URL = 'https://api.sendgrid.com/api/mail.send.json'

    def __init__(self, settings):
        self._user = settings['sendgrid.user']
        self._key = settings['sendgrid.password']
        self._from_addr = settings['from.email']
        self._from_name = settings['from.name']
        self._subject = settings['email.subject']
        self._cc = settings.get('email.cc')
        self._bcc = settings.get('email.bcc')

    def _create_smtpapi(self):
        smtpapi = {
            'category': ['translation-validator'],
            'ts': int(time()),
            'unique_args': {
                'reason': 'translation-validator',
                'template': 'translation-validator',
                'tid': 'custom:translation-validator'
            }
        }
        return json.dumps(smtpapi)

    def _create_query(self, recipient, html):
        query = {
            'api_user': self._user,
            'api_key': self._key,
            'from': self._from_addr,
            'fromname': self._from_name,
            'to': recipient,
            'subject': self._subject,
            'html': html
        }
        if self._cc:
            query['cc'] = self._cc.split(',')
        if self._bcc:
            query['bcc'] = self._bcc.split(',')
        return query

    async def _handle_response(self, res):
        content = await res.read()
        if res.status in [200, 201]:
            return True
        if res.status == 400:
            logger.warning('bad request %s, data: %s', res.status, content)
            return True
        else:
            logger.error('SendGrid request failed: %s %s', res.status, content)
            return False

    async def send(self, recipient, html):
        if not recipient:
            return True

        query = self._create_query(recipient, html)
        query['x-smtpapi'] = self._create_smtpapi()
        async with aiohttp.ClientSession() as session:
            logger.debug('sending email to %s', recipient)
            async with session.post(self.URL, data=query) as res:
                result = await self._handle_response(res)
                return result
