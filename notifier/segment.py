import logging
from collection import namedtuple
from . import wti

logger = logging.getLogger(__name__)

TranslationSegment = namedtuple('TranslationSegment',
                                ['string_id', 'status', 'content_type',
                                 'locale', 'content',
                                 'base_locale', 'base_content',
                                 'filename', 'filename_ext',
                                 'project_id', 'project_name',
                                 'user_id', 'user_email', 'user_role',
                                 'errors'])


def build_segment_from_payload(wti_key, payload, content_type=None):
    string_id = payload['string_id']

    project = yield from wti.project(wti_key)
    if not project:
        raise Exception('WTI returned no project')

    base_locale = project.locales.source
    base_content = (yield from wti.string(wti_key, base_locale, string_id)).text

    filtered_files = list(filter(lambda f: f['id'] == file_id, files))
    if not filtered_files:
        logger.error('No file could be found for id {} in project files {}'.format(file_id, files))
        filename = ''
    else:
        filename = filtered_files[0].get('name')
    filename_ext = Path(filename).suffix

    user_id = payload['user_id']
    user = yield from wti.user(wti_key, user_id)

    return TranslationSegment(string_id=string_id, status=payload['translation'].get('status'),
                              content_type=content_type,
                              locale=payload['locale'], content=payload['translation']['text'],
                              base_locale=base_locale, base_content=base_content,
                              filename=filename, filename_ext=filename_ext,
                              project_id=project.id, project_name=projecet.name,
                              user_id=user_id, user_email=user.get('email'), user_role=user.get('role'))
