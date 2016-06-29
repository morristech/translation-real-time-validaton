from bs4 import BeautifulSoup
import inlinestyler.utils as inline_styler
import markdown
import logging
import asyncio
import json
import os.path
import aiohttp
from pybars import Compiler

logger = logging.getLogger(__name__)


def _read_template_file(name):
    path = os.path.join('./notifier/templates/', name)
    with open(path, 'r') as fp:
        return fp.read()


def _parse_diff_error(diff, content_type):
    base_html = markdown.markdown(diff.diff.base.parsed)
    other_html = markdown.markdown(diff.diff.other.parsed)

    template_vars = {
        'error_messages': diff.diff.error_msgs,
        'left_path': diff.file_path + diff.base_path,
        'right_path': diff.other_path,
        'left_html': BeautifulSoup(base_html).body,
        'right_html': BeautifulSoup(other_html).body,
        'section_link': diff.section_link
    }
    if content_type == 'md':
        template_vars['left_diff'] = BeautifulSoup(diff.diff.base.diff).body,
        template_vars['right_diff'] = BeautifulSoup(diff.diff.other.diff).body

    return template_vars


@asyncio.coroutine
def send(mailman_endpoint, user_email, diffs, url_errors, content_type, topic=None):
    template_source = _read_template_file('base_error.hbs')

    template = Compiler().compile(template_source)({
        'diff_errors': [_parse_diff_error(diff, content_type) for diff in diffs],
        'url_errors': url_errors,
        'css': _read_template_file('basic.css')
    })
    email_body = inline_styler.inline_css(template)
    message = {
        'from_addr': 'no-reply@getkeepsafe.com',
        'from_name': 'KeepSafe Translation Verifier',
        'subject': topic or 'Translations not passing the validation test',
        'html': email_body,
        'to': user_email,
        'cc': ['philipp+content-validator@getkeepsafe.com'],
        'bcc': ['tomek+content-validator@getkeepsafe.com']
    }
    if content_type == 'java':
        message['bcc'].append('hilal+content-validator@getkeepsafe.com')

    try:
        res = yield from asyncio.wait_for(
            aiohttp.request('post', mailman_endpoint, data=json.dumps(message)),
            5)
        return res.status == 200
    except asyncio.TimeoutError:
        logging.error('Request to %s took more then 5s to finish, dropping', mailman_endpoint)
    return False
