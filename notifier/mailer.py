from bs4 import BeautifulSoup
import inlinestyler.utils as inline_styler
import markdown
import logging
import asyncio
import os.path
import aiohttp
from pybars import Compiler

logger = logging.getLogger(__name__)
SEND_EMAIL_PATH = 'emails/send_raw'


def _inner_html(html):
    soup = BeautifulSoup(html, "lxml").body
    return ''.join(map(lambda t: str(t), soup.contents))


def _read_template_file(name):
    path = os.path.join('./notifier/templates/', name)
    with open(path, 'r') as fp:
        return fp.read()


def _parse_diff_error(diff, content_type):
    base_html = markdown.markdown(diff.diff.base.parsed)
    other_html = markdown.markdown(diff.diff.other.parsed)

    template_vars = {
        'error_messages': list(diff.diff.error_msgs),
        'left_path': diff.file_path + diff.base_path,
        'right_path': diff.other_path,
        'left_html': _inner_html(base_html),
        'right_html': _inner_html(other_html),
        'section_link': diff.section_link
    }
    if content_type == 'md':
        template_vars['left_diff'] = _inner_html(diff.diff.base.diff)
        template_vars['right_diff'] = _inner_html(diff.diff.other.diff)

    return template_vars


@asyncio.coroutine
def send(mail_client, user_email, diffs, url_errors, content_type, topic=None):
    template_source = _read_template_file('base_error.hbs')

    template = Compiler().compile(template_source)({
        'diff_errors': [_parse_diff_error(diff, content_type) for diff in diffs],
        'url_errors': url_errors,
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
