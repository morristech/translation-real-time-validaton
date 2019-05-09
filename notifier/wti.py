import aiohttp
import logging
import json

from .model import *
from . import httpclient

logger = logging.getLogger(__name__)


class WtiClient:
    host = 'https://webtranslateit.com/api/projects/'
    headers = {'content-type': 'application/json'}

    def __init__(self, api_key=None):
        self._api_key = None
        if api_key:
            self.set_project_key(api_key)
        self._client = httpclient.HttpClient(self.host, max_retries=3, headers=self.headers)

    async def shutdown(self):
        await self._client.close()

    async def bootstrap(self):
        await self._client.bootstrap()

    def set_project_key(self, api_key):
        self._api_key = api_key

    def _handle_response(self, url, ex):
        status = getattr(ex, 'status', 0)
        message = getattr(ex, 'message', '')
        if status == 404:
            logger.debug('data does not exist for url:%s', url)
            return {}
        else:
            raise WtiError(status, message)

    async def _request_data(self, url):
        logger.debug('getting wti data url:%s', url)
        try:
            data = await self._client.get(url)
            return data
        except aiohttp.ClientError as ex:
            self._handle_response(url, ex)

    async def _update_data(self, url, data):
        logger.debug('updating wti data url:%s', url)
        try:
            await self._client.post(url, data=json.dumps(data))
            return data
        except aiohttp.ClientError as ex:
            self._handle_response(url, ex)
        return False

    async def string(self, string_id, locale):
        url = '/%s/strings/%s/locales/%s/translations.json' % (self._api_key, string_id, locale)
        data = await self._request_data(url)
        if data:
            return WtiString(data['id'], data['locale'], data['text'], WtiTranslationStatus(data['status']),
                             data['updated_at'])
        else:
            return {}

    async def create_string(self, dc_item, default_locale):
        url = '/%s/strings' % self._api_key
        data = {
            'key': dc_item.key,
            'plural': False,
            'type': 'String',
            'dev_comment': dc_item.zendesk_item.name,
            'translations': [{
                'locale': default_locale,
                'text': dc_item.zendesk_item.text,
                'status': WtiTranslationStatus.proofread.value
            }]
        }
        await self._update_data(url, data)

    async def strings_ids(self):
        url = '/%s/strings.json' % self._api_key
        data = await self._client.request('GET', url, follow_links=True)
        return {item['key']: item['id'] for item in data}

    async def user(self, user_id):
        url = '/%s/users.json' % self._api_key
        users = await self._request_data(url)
        for user in users:
            if user.get('user_id') == user_id:
                return WtiUser(user['user_id'], user['email'], WtiUserRoles[user['role']])
        logger.error('unable to get user with id %s', user_id)
        return WtiUser(0, None, None)

    async def change_status(self, translated_string, status=WtiTranslationStatus.unverified):
        url = '/%s/strings/%s/locales/%s/translations' % (self._api_key, translated_string.id, translated_string.locale)
        data = {'text': translated_string.text, 'status': status.value, 'minor_change': False, 'validation': False}
        res = await self._update_data(url, data)
        return res

    def _filename(self, files, file_id):
        for file in files:
            if file['id'] == file_id:
                return file['name']
        logger.warning('No file could be found for id {} in project files {}'.format(file_id, files))
        return ''

    async def get_project(self):
        data = await self._request_data(self._api_key + '.json')
        try:
            project_data = data['project']
            return project_data
        except Exception:
            logger.exception('Unexpected response from WTI %s', data)

    async def project(self, file_id, content_type):
        data = await self._request_data(self._api_key + '.json')
        try:
            project_data = data['project']
            master_locale = project_data['source_locale']['code']
            project_name = project_data['name']
            project_id = project_data['id']
            filename = self._filename(project_data['project_files'], file_id)
            return WtiProject(project_id, project_name, master_locale, filename, content_type)
        except KeyError:
            logger.exception('Unexpected response from WTI %s', data)

    def section_link(self, project, translated_string):
        section_url = 'https://webtranslateit.com/en/projects/%s-%s/locales/%s..%s/strings/%s'
        return section_url % (project.id, project.name, project.master_locale, translated_string.locale,
                              translated_string.id)

    async def update_translation(self, string_id, text, locale, validation=True):
        url = '/%s/strings/%s/locales/%s/translations.json' % (self._api_key, string_id, locale)
        data = {
            'text': text,
            'status': WtiTranslationStatus.proofread.value,
            'minor_change': False,
            'validation': validation
        }
        await self._update_data(url, data)
