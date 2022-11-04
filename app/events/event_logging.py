import logging

class EventLoggingAdapter(logging.LoggerAdapter):
    def __init__(self, event_name, logger):
        super(EventLoggingAdapter, self).__init__(logger, {})
        self.event_name = event_name
        self.line_num = 0

    def process(self, msg, kwargs):
        return '[(%s):Line %d] %s' % (self.event_name, self.line_num, msg), kwargs