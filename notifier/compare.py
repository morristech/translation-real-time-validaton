from validator import checks
import asyncio


@asyncio.coroutine
def diff(base, other):
    md_check = checks.markdown()
    return md_check._compare(base, other)
