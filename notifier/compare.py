import validator
import validator.checks
import asyncio


@asyncio.coroutine
def diff(base, other, content_type='md'):
    if content_type == 'md':
        return _md_diff(base, other)
    if content_type == 'java':
        return _java_diff(base, other)
    raise ValueError('unknown content type')


def _md_diff(base, other):
    return validator.parse().text(base, other).check().md().validate()


def _java_diff(base, other):
    return validator.parse().text(base, other).check().java().validate()
