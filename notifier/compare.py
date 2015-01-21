from validator import checks
import asyncio


@asyncio.coroutine
def diff(base, other):
    print(base)
    print(other)
    md_check = checks.markdown()
    return md_check._compare(base, other)
