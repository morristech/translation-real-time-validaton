from enum import Enum
from collections import namedtuple

WtiUser = namedtuple('WtiUser', ['id', 'email', 'role'])
WtiProject = namedtuple('WtiProject', ['id', 'name', 'master_locale', 'filename', 'content_type'])
WtiString = namedtuple('WtiString', ['id', 'locale', 'text', 'status'])

ZendeskItem = namedtuple('ZendeskItem', ['id', 'name', 'text', 'variants'])
DynamicContentItem = namedtuple('DynamicContentItem', ['key', 'wti_id', 'zendesk_item'])

DiffError = namedtuple('DiffError', ['url_errors', 'md_error', 'section_link'])


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
    pass
