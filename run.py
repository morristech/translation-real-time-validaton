import asyncio
import notifier
import configparser
import logging
from aiohttp import log


def read_keys():
    config = configparser.ConfigParser()
    config.read('srv.ini')
    return dict(config[config.default_section])

logger = log.web_logger

logging.getLogger('asyncio').setLevel(logging.ERROR)
log.access_logger.setLevel(logging.INFO)

hlr = logging.handlers.RotatingFileHandler('/var/log/translation-validator.log', maxBytes=10000000)
logger.addHandler(hlr)

syslog = logging.handlers.SysLogHandler(address=('logs.papertrailapp.com', 36172))
formatter = logging.Formatter('%(asctime)s %(hostname)s TRANSLATION-VALIDATOR %(message)s', datefmt='%Y-%m-%dT%H:%M:%S')
syslog.setFormatter(formatter)
logger.addHandler(syslog)

accessHlr = logging.handlers.RotatingFileHandler('/var/log/translation-validator_access.log', maxBytes=10000000)
log.access_logger.addHandler(accessHlr)

keys = read_keys()
app = notifier.main({}, **keys)
f = app.loop.create_server(app.make_handler(access_log=log.access_logger), '0.0.0.0', 5001)
srv = app.loop.run_until_complete(f)
print('serving on', srv.sockets[0].getsockname())
try:
    app.loop.run_forever()
except KeyboardInterrupt:
    pass
