import asyncio
import notifier
import configparser
from aiohttp import log


def read_keys():
    config = configparser.ConfigParser()
    config.read('srv.ini')
    return dict(config[config.default_section])


keys = read_keys()
app = notifier.main({}, **keys)
f = app.loop.create_server(app.make_handler(access_log=log.access_logger), '0.0.0.0', 5001)
srv = app.loop.run_until_complete(f)
print('serving on', srv.sockets[0].getsockname())
try:
    app.loop.run_forever()
except KeyboardInterrupt:
    pass
