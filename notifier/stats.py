import logging
import datadog

logger = logging.getLogger(__name__)


class Stats:
    _prefix = 'keepsafe.trasnlations.%s'

    def __init__(self, api_key):
        datadog.initialize(api_key=api_key)
        self._handler = datadog.statsd

    def increment(self, name, *args, **kwargs):
        metric_name = self._prefix % name
        self._handler.increment(metric_name, *args, **kwargs)
