from enum import Enum
from collections import namedtuple

WtiUser = namedtuple('WtiUser', ['id', 'email', 'role'])
WtiProject = namedtuple('WtiProject', ['id', 'name', 'master_locale', 'filename', 'content_type'])
WtiString = namedtuple('WtiString', ['id', 'locale', 'text', 'status', 'updated_at'])

ZendeskItem = namedtuple('ZendeskItem', ['id', 'name', 'text', 'variants'])
DynamicContentItem = namedtuple('DynamicContentItem', ['key', 'wti_id', 'zendesk_item'])

DiffError = namedtuple('DiffError', ['url_errors', 'md_error', 'section_link'])

GoogleTranslation = namedtuple('GoogleTranslation', [
    'translatedText',
    'model',
    'detectedSourceLanguage',
])
GoogleTranslation.__new__.__defaults__ = (None,)

GoogleLanguage = namedtuple('GoogleLanguage', [
    'language',
    'name'
])
GoogleLanguage.__new__.__defaults__ = (None,)


class WtiUserRoles(Enum):
    translator = 'translator'
    manager = 'manager'
    client = 'client'


class WtiTranslationStatus(Enum):
    untranslated = 'status_untranslated'
    unverified = 'status_unverified'
    unproofread = 'status_unproofread'
    proofread = 'status_proofread'
    hidden = 'status_hidden'


class WtiContentTypes(Enum):
    ios = 'ios'
    md = 'md'
    java = 'java'


class WtiError(Exception):
    def __init__(self, parent_ex):
        self.request_info = getattr(parent_ex, 'request_info', None)
        self.status = getattr(parent_ex, 'status', None)
        self.message = getattr(parent_ex, 'message', None)

    def __str__(self):
        return 'WTI API error, status: %s, message:%s, request: %s' % (self.status, self.message, self.request_info)


class TranslationError(Exception):
    def __init__(self, parent_ex, req_params):
        self.request_info = getattr(parent_ex, 'request_info', None)
        self.status = getattr(parent_ex, 'status', None)
        self.message = getattr(parent_ex, 'message', None)
        self.req_params = req_params

    def __str__(self):
        return 'Translator failed, status: %s, message: %s, request: %s' % (self.status, self.message,
                                                                            self.request_info)


class UnknownResponse(Exception):
    def __init__(self, resp_data):
        self.resp_data = resp_data

    def __str__(self):
        return 'Unknown response format: %s' % self.resp_data


class UnsupportedLocale(Exception):
    def __init__(self, locale):
        self._locale = locale

    def __str__(self):
        return 'Unsupported locale: %s' % self._locale
