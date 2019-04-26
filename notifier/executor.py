import asyncio
from functools import partial


class AsyncWrapper:
    def __init__(self, target_instance, executor=None):
        self._target_inst = target_instance
        self._loop = asyncio.get_event_loop()
        self._executor = executor

    def __getattribute__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            method = self._target_inst.__getattribute__(name)
            return partial(self._async_wrapper, method)

    @asyncio.coroutine
    def _async_wrapper(self, method_name, *args, **kwargs):
        boto_call = partial(method_name, *args, **kwargs)
        return self._loop.run_in_executor(self._executor, boto_call)
