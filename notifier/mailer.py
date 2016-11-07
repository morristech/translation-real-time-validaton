import inlinestyler.utils as inline_styler
import logging
import asyncio
import os.path
import aiohttp
from pybars import Compiler

logger = logging.getLogger(__name__)
SEND_EMAIL_PATH = 'emails/send_raw'


def _read_template_file(name):
    path = os.path.join('./notifier/templates/', name)
    with open(path, 'r') as fp:
        return fp.read()


@asyncio.coroutine
def send(mail_client, user_email, segments, content_type, topic=None):
    template_source = _read_template_file('base_error.hbs')
    template = Compiler().compile(template_source)({
        'segments': segments,
        'css': _read_template_file('basic.css')
    })
    email_body = inline_styler.inline_css(template)
    message = {
        'subject': topic or 'Translations not passing the validation test',
        'html': email_body,
        'to': user_email,
        'cc': ['julie+content-validator@getkeepsafe.com'],
        'bcc': ['tomek+content-validator@getkeepsafe.com']
    }
    if content_type == 'java':
        message['bcc'].append('hilal+content-validator@getkeepsafe.com')
    try:
        res = yield from mail_client.send(**message)
        if res.status != 200:
            msg = yield from res.read()
            logger.error(
                'unable to send email, status: %s, message: %s', res.status, msg)
            return False
        else:
            yield from res.release()
            return True
    except aiohttp.ClientOSError:
        logging.error('Request to sendgrid failed')
    return False
