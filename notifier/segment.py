import logging
from collections import namedtuple
from pathlib import Path
from . import wti

logger = logging.getLogger(__name__)

TranslationSegmentBase = namedtuple('TranslationSegmentBase',
                                    ['string_id', 'status', 'content_type',
                                     'locale', 'content',
                                     'base_locale', 'base_content',
                                     'filename', 'filename_ext',
                                     'project_id', 'project_name',
                                     'user_id', 'user_email', 'user_role',
                                     'diff_errors', 'url_errors'])


class TranslationSegment(TranslationSegmentBase):
    SECTION_URL = 'https://webtranslateit.com/en/projects/{project_id}-{project_name}/locales/\
{master_locale}..{other_locale}/strings/{string_id}'

    @property
    def section_link(self):
        return self.SECTION_URL.format(project_id=self.project_id, project_name=self.project_name,
                                       master_locale=self.base_locale, other_locale=self.locale,
                                       string_id=self.string_id)


def build_segment_from_payload(wti_key, payload, content_type=None):
    string_id = payload['string_id']

    project = yield from wti.project(wti_key)
    if not project:
        raise Exception('WTI returned no project')

    base_locale = project.locales.source
    base_content = (yield from wti.string(wti_key, base_locale, string_id)).text

    filename, filename_ext = _resolve_filename_and_ext(project.files, payload['file_id'])
    user_id = payload['user_id']
    user = yield from wti.user(wti_key, user_id)

    return TranslationSegment(string_id=string_id, status=payload['translation'].get('status'),
                              content_type=content_type,
                              locale=payload['locale'], content=payload['translation']['text'],
                              base_locale=base_locale, base_content=base_content,
                              filename=filename, filename_ext=filename_ext,
                              project_id=project.id, project_name=project.name,
                              user_id=user_id, user_email=user.get('email'), user_role=user.get('role'),
                              diff_errors=[], url_errors=[])


def build_segment(project, string, base_translation, other_translation, user_email, content_type='md'):
    filename, filename_ext = _resolve_filename_and_ext(project.files, string.id)

    return TranslationSegment(string_id=string.id, status=None,
                              content_type=content_type,
                              locale=other_translation.locale, content=other_translation.text,
                              base_locale=base_translation.locale, base_content=base_translation.text,
                              filename=filename, filename_ext=filename_ext,
                              project_id=project.id, project_name=project.name,
                              user_id=None, user_email=user_email, user_role=None,
                              diff_errors=[], url_errors=[])


def _resolve_filename_and_ext(files, file_id):
    filtered_files = list(filter(lambda f: f['id'] == file_id, files))
    if not filtered_files:
        logger.error('No file could be found for id {} in project files {}'.format(file_id, files))
        filename = ''
    else:
        filename = filtered_files[0].get('name')
    return (filename, Path(filename).suffix)
