from . import compare


class BaseValidator:
    change_status = True
    notify_agent = True

    @classmethod
    def match(cls, segment):
        True

    def __init__(self, segment):
        self.segment = segment
        self.url_errors = []
        self.diff_errors = []

    def validate(self):
        return True

    def _add_diff_err(self, err):
        # deal with content-validator result
        pass

    def _add_url_err(self, err):
        pass


class NoopValidator:
    @classmethod
    def match(cls, segment):
        segment.status == 'status_proofread' or segment.filename_ext == '.strings'


class IosValidator:
    @classmethod
    def match(cls, segment):
        return segment.content_type == 'ios' and segment.filename_ext == '.txt'


def dispatch(segment, order=[NoopValidator, IosValidator]):
    for validator in order:
        if validator.match(segment):
            return validator
    return None
