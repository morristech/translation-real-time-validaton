import logging
import asyncio
import markdown
from bs4 import BeautifulSoup
from collections import namedtuple
from . import compare

logger = logging.getLogger(__name__)

DiffError = namedtuple('DiffError', ['base_html', 'other_html', 'base_diff', 'other_diff', 'error_messages'])
UrlError = namedtuple('UrlError', ['url', 'status_code', 'has_disallowed_chars'])


class BaseValidator:
    change_status = True
    notify_agent = True

    @classmethod
    def match(cls, segment):
        return True

    def __init__(self, segment):
        self.segment = segment

    @asyncio.coroutine
    def validate(self):
        return True

    def _add_diff_error(self, error):
        base_md = markdown.markdown(error.base.parsed)
        other_md = markdown.markdown(error.other.parsed)

        base_html = _inner_html(base_md),
        other_html = _inner_html(other_md),

        base_diff = other_diff = None
        if self.segment.content_type == 'md':
            base_diff = _inner_html(error.base.diff)
            other_diff = _inner_html(error.other.diff)

        diff_error = DiffError(base_html, other_html, base_diff, other_diff, error.error_msgs)
        self.segment.diff_errors.append(diff_error)

    def _add_url_error(self, error):
        url_error = UrlError(error.url, error.status_code, error.has_disallowed_chars)
        self.segment.url_errors.append(url_error)


class NoopValidator(BaseValidator):

    @classmethod
    def match(cls, segment):
        segment.status == 'status_proofread' or segment.filename_ext == '.strings'


class IosValidator(BaseValidator):

    @classmethod
    def match(cls, segment):
        return segment.content_type == 'ios' and segment.filename_ext == '.txt'

    @asyncio.coroutine
    def validate(self):
        errors = yield from compare.urls(self.segment.base_content, self.segment.content)
        for error in errors:
            self._add_url_error(error)
        return len(errors) == 0


class MdStructureValidator(BaseValidator):

    @asyncio.coroutine
    def validate(self):
        errors = yield from compare.diff(self.segment.base_content,
                                         self.segment.content,
                                         self.segment.content_type)
        for error in errors:
            self._add_diff_error(error)
        return len(errors) == 0


def dispatch(segment, order=[NoopValidator, IosValidator, MdStructureValidator]):
    for validator in order:
        if validator.match(segment):
            return validator
    return None


def _inner_html(html):
    soup = BeautifulSoup(html, "lxml").body
    return ''.join(map(lambda t: str(t), soup.contents))
