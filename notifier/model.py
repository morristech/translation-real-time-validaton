from enum import Enum
from collections import namedtuple

WtiUser = namedtuple('WtiUser', ['id', 'email', 'role'])
WtiProject = namedtuple('WtiProject', ['id', 'name', 'master_locale', 'filename', 'content_type'])
WtiString = namedtuple('WtiString', ['id', 'text', 'locale'])
WtiTranslation = namedtuple('WtiTranslation', ['id', 'locale', 'text'])

DiffError = namedtuple('DiffError', ['url_errors', 'md_error', 'section_link'])


class WtiUserRoles(Enum):
    translator = 'translator'
    manager = 'manager'
    client = 'client'


class WtiTranslationStatus(Enum):
    unverified = 'status_unverified'
    proofread = 'status_proofread'


class WtiContentTypes(Enum):
    ios = 'ios'
    md = 'md'
    java = 'java'


class WtiConnectionError(Exception):
    pass
