import validator
import validator.checks
import asyncio


@asyncio.coroutine
def diff(base, other):
    return validator.parse().text(base, other).check().md().validate()
