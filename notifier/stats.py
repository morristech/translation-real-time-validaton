import logging
import datadog

logger = logging.getLogger(__name__)


class Stats:
    _prefix = 'keepsafe.translations.%s'

    def __init__(self, api_key, app_key):
        datadog.initialize(api_key=api_key, app_key=app_key)
        self._handler = datadog.statsd

    def increment(self, name, value=1, **tags):
        metric_name = self._prefix % name
        tags_fmt = ['%s:%s' % (k, v) for k, v in tags.items()]
        self._handler.increment(metric_name, value, tags=tags_fmt)

    def gauge(self, name, value, **tags):
        metric_name = self._prefix % name
        tags_fmt = ['%s:%s' % (k, v) for k, v in tags.items()]
        self._handler.gauge(metric_name, value, tags=tags_fmt)
