import logging
import simplejson
import time
import aiohttp

from . import const

logger = logging.getLogger(__name__)


class SendgridProvider:

    URL = 'https://api.sendgrid.com/api/mail.send.json'

    def __init__(self, user, key, from_addr, from_name, *,
                 loop=None):
        self._user = user
        self._key = key
        self._from_addr = from_addr
        self._from_name = from_name
        self._loop = loop

    def send(self, subject, html, to, args=None, categories=None, cc=None, bcc=None):
        """
        categories is array
        args dictionary is passed as x-smtpapi unique_args json
        """
        query = {
            'api_user': self._user,
            'api_key': self._key,
            'from': self._from_addr,
            'fromname': self._from_name,
            'to': to,
            'subject': subject,
            'html': html
        }
        if cc:
            query['cc'] = cc
        if bcc:
            query['bcc'] = bcc

        smtpapi = {}
        smtpapi['ts'] = int(time.time())
        if args:
            smtpapi['unique_args'] = args
        if categories:
            smtpapi['category'] = categories
        query['x-smtpapi'] = simplejson.dumps(smtpapi)

        with aiohttp.ClientSession() as session:
            res = yield from session.post(self.URL, data=query)
            return res
        content = yield from res.read()
        if res.status in [200, 201]:
            return True, ''
        if res.status == 400:
            logger.warning('bad request %s, data: %s', res.status, content)
            return True, ''
        else:
            logger.error('SendGrid request failed: %s %s', res.status, content)
            return False, self._extract_status(content)

    def _extract_status(self, data):
        try:
            data = simplejson.loads(data.decode(const.ENCODING, 'replace'))
            return data['errors'][0]
        except:
            logger.error('SendGrid error: %r', data)
            return 'unknown error'
