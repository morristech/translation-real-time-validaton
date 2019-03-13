import aiohttp
import logging
import json

from .model import *

logger = logging.getLogger(__name__)

TRANSLATION_URL = 'https://webtranslateit.com/api/projects/%s/strings/%s/locales/%s/translations.json'
USERS_URL = 'https://webtranslateit.com/api/projects/%s/users.json'
STATUS_URL = 'https://webtranslateit.com/api/projects/%s/strings/%s/locales/%s/translations'
PROJECT_URL = 'https://webtranslateit.com/api/projects/%s.json'
STRINGS_URL = 'https://webtranslateit.com/api/projects/%s/strings.json'
CREATE_STRING_URL = 'https://webtranslateit.com/api/projects/%s/strings'
SECTION_URL = 'https://webtranslateit.com/en/projects/%s-%s/locales/%s..%s/strings/%s'


# TODO user httpclient
class WtiClient:
    def __init__(self, api_key):
        self._api_key = api_key

    def _next_page_link(self, headers):
        header = headers.get('Link')
        if header:
            for link in header.split(','):
                bits = link.split(';')
                if bits[1].strip() == 'rel="next"':
                    return bits[0].strip('<>')
        return ''

    async def _handle_response(self, url, res):
        if res.status == 200:
            data = await res.json()
            return data
        elif res.status in [502, 503]:
            await res.release()
            logger.warning('wti request timed out for url:%s', url)
            return {}
        elif res.status == 404:
            await res.release()
            logger.debug('data does not exist for url:%s', url)
            return {}
        else:
            msg = await res.read()
            raise WtiError('unable to connect to wti, status: %s, message:%s' % (res.status, msg))

    async def _request_data(self, url):
        logger.debug('getting wti data url:%s', url)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as res:
                data = await self._handle_response(url, res)
                return data

    async def _request_paging_data(self, url):
        logger.debug('getting wti data url:%s', url)
        result = []
        async with aiohttp.ClientSession() as session:
            for i in range(10):
                async with session.get(url) as res:
                    data = await self._handle_response(url, res)
                    result.extend(data)
                    url = self._next_page_link(res.headers)
                    if not url:
                        break
        return result

    async def _update_data(self, url, data):
        logger.debug('updating wti data url:%s', url)
        headers = {'content-type': 'application/json'}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=json.dumps(data), headers=headers, timeout=5) as res:
                if res.status in [200, 201, 202]:
                    return True
                else:
                    msg = await res.text()
                    logger.error('request to wti failed status:%s, message: %s', res.status, msg)
        return False

    async def string(self, string_id, locale):
        url = TRANSLATION_URL % (self._api_key, string_id, locale)
        data = await self._request_data(url)
        if data:
            return WtiString(data['id'], data['locale'], data['text'])
        else:
            return {}

    async def create_string(self, dc_item, default_locale):
        url = CREATE_STRING_URL % self._api_key
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
        url = STRINGS_URL % self._api_key
        data = await self._request_paging_data(url)
        return {item['key']: item['id'] for item in data}

    async def user(self, user_id):
        url = USERS_URL % self._api_key
        users = await self._request_data(url)
        for user in users:
            if user.get('user_id') == user_id:
                return WtiUser(user['user_id'], user['email'], WtiUserRoles[user['role']])
        logger.error('unable to get user with id %s', user_id)
        return WtiUser(0, None, None)

    async def change_status(self, translated_string, status=WtiTranslationStatus.unverified):
        data = {'text': translated_string.text, 'status': status.value, 'minor_change': False}
        url = STATUS_URL % (self._api_key, translated_string.id, translated_string.locale)
        res = await self._update_data(url, data)
        return res

    def _filename(self, files, file_id):
        for file in files:
            if file['id'] == file_id:
                return file['name']
        logger.error('No file could be found for id {} in project files {}'.format(file_id, files))
        return ''

    async def project(self, file_id, content_type):
        url = PROJECT_URL % self._api_key
        data = await self._request_data(url)
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
        return SECTION_URL % (project.id, project.name, project.master_locale, translated_string.locale,
                              translated_string.id)

    async def update_translation(self, dc_item, locale):
        url = TRANSLATION_URL % (self._api_key, dc_item.wti_id, locale)
        data = {
            'text': dc_item.zendesk_item.text,
            'status': WtiTranslationStatus.proofread.value,
            'minor_change': False
        }
        await self._update_data(url, data)
