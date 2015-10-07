import validator
import validator.checks
import asyncio


@asyncio.coroutine
def diff(base, other):
    checks = [validator.checks.markdown()]
    return validator.validate_text(checks, base, other)
