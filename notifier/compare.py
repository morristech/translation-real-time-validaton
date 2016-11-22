import validator
import validator.checks
import os
import hashlib

from . import const
from .model import *


def diff(wti_client, project, base, other):
    _, filename_ext = os.path.splitext(project.filename)
    section_link = wti_client.section_link(project, other)
    if filename_ext == '.strings':
        return None
    elif project.content_type == WtiContentTypes.ios and filename_ext == '.txt':
        return DiffError(_urls(base.text, other.text), None, section_link)
    elif project.content_type == WtiContentTypes.java:
        return DiffError(None, _java_diff(base.text, other.text), section_link)
    else:
        md_errors = _md_diff(base.text, other.text)
        md_error = md_errors[0] if len(md_errors) > 0 else None
        return DiffError(_urls(base.text, other.text), md_error, section_link)


def _urls(base, other):
    return validator.parse().text(base, other).check().url().validate()


def _md_diff(base, other):
    return validator.parse().text(base, other).html().check().md().validate()


def _java_diff(base, other):
    return validator.parse().text(base, other).check().java().validate()


def is_different(text1, text2):
    hash1 = hashlib.md5()
    hash1.update(text1.encode(const.ENCODING))
    hash1 = hash1.hexdigest()

    hash2 = hashlib.md5()
    hash2.update(text2.encode(const.ENCODING))
    hash2 = hash2.hexdigest()

    return hash1 == hash2
