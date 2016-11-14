import aiohttp
import asyncio
import json
import logging

from .model import *

logger = logging.getLogger(__name__)

TRANSLATION_URL = 'https://webtranslateit.com/api/projects/%s/strings/%s/locales/%s/translations.json'
USERS_URL = 'https://webtranslateit.com/api/projects/%s/users.json'
STATUS_URL = 'https://webtranslateit.com/api/projects/%s/strings/%s/locales/%s/translations'
PROJECT_URL = 'https://webtranslateit.com/api/projects/%s.json'
STRINGS_URL = 'https://webtranslateit.com/api/projects/%s/strings.json'
SECTION_URL = 'https://webtranslateit.com/en/projects/%s-%s/locales/%s..%s/strings/%s'


class WtiClient:
    def __init__(self, api_key):
        self._api_key = api_key

    async def _request_data(self, url):
        with aiohttp.ClientSession() as session:
            res = await session.get(url)
            if res.status == 200:
                data = await res.json()
                return data
            else:
                msg = await res.read()
                raise WtiConnectionError('unable to contact wti, status: %s, message:%s' % (res.status, msg))

    async def string(self, string_id, locale):
        url = TRANSLATION_URL % (self._api_key, locale, string_id)
        data = await self._request_data(url)
        return WtiString(data['id'], data['text'], data['locale'])

    async def strings(self):
        raise NotImplementedError()
        url = STRINGS_URL % self._api_key
        data = await self._request_data(url)
        return [WtiString(s['id'], s['text'], s['locale']) for s in data]

    async def user(self, user_id):
        url = USERS_URL % self._api_key
        users = await self._request_data(url)
        for user in users:
            if user.get('user_id') == user_id:
                return WtiUser(user['user_id'], user['email'], WtiUserRoles[user['role']])
        logger.error('unable to get user with id %s', user_id)
        return WtiUser(0, None, None)

    async def change_status(self, translated_string, status=WtiTranslationStatus.unverified):
        message = json.dumps({'text': translated_string.text, 'status': status.value, 'minor_change': False})
        headers = {'content-type': 'application/json'}
        url = STATUS_URL % (self._api_key, translated_string.locale, translated_string.id)
        try:
            with aiohttp.ClientSession() as session:
                res = await asyncio.wait_for(session.post(url, data=message, headers=headers), 5)
                await res.release()
                if res.status in [200, 202]:
                    return True
                else:
                    logger.error('request to wti failed status:%s', res.status)
        except asyncio.TimeoutError:
            logging.error('Request to {} took more then 5s to finish, dropping'.format(url))
        return False

    def _filename(self, files, file_id):
        for file in files:
            if file['id'] == file_id:
                return file['name']
        logger.error('No file could be found for id %s in project files {}'.format(file_id, files))
        return ''

    async def project(self, file_id, content_type):
        url = PROJECT_URL % self._api_key
        data = await self._request_data(url)
        project_data = data['project']
        master_locale = project_data['source_locale']['code']
        project_name = project_data['name']
        project_id = project_data['id']
        filename = self._filename(project_data['project_files'], file_id)
        return WtiProject(project_id, project_name, master_locale, filename, content_type)

    def section_link(self, project, translated_string):
        return SECTION_URL % (project.id, project.name, project.master_locale, translated_string.locale,
                              translated_string.id)
