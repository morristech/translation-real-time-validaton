import aiohttp
import asyncio
import json
import logging
from aiohttp import log
from parse import parse
from functools import partial
from collections import namedtuple

logger = log.web_logger

translation_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/strings/{string_id}/locales/{locale}/translations.json'
users_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/users.json'
status_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/strings/{string_id}/locales/{locale}/translations'
project_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}.json'
strings_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/strings.json'

Locales = namedtuple('Locales', ['source', 'targets'])
Project = namedtuple('Project', ['locales', 'files', 'name', 'id'])
String = namedtuple('String', ['id', 'file_id'])
Translation = namedtuple('Translation', ['id', 'locale', 'text'])


def string(api_key, locale, string_id):
    url = translation_url_pattern.format(api_key=api_key, locale=locale, string_id=string_id)
    res = yield from aiohttp.request('get', url)
    data = yield from res.json()
    return Translation(id=string_id, locale=locale, text=data.get('text', ''))


def strings(api_key):
    url = strings_url_pattern.format(api_key=api_key)
    res = yield from aiohttp.request('get', url)
    data = yield from res.json()
    return (String._make([s['id'], s['file']['id']]) for s in data)


def user(api_key, user_id):
    url = users_url_pattern.format(api_key=api_key)
    res = yield from aiohttp.request('get', url)
    users = yield from res.json()
    for user in users:
        if user['user_id'] == user_id:
            return user
    return {}


def change_status(api_key, locale, string_id, text, status='status_unverified'):
    message = json.dumps({
        'text': text,
        'status': status,
        'minor_change': False
    })
    headers = {'content-type': 'application/json'}
    url = status_url_pattern.format(api_key=api_key, locale=locale, string_id=string_id)
    try:
        res = yield from asyncio.wait_for(aiohttp.request('post', url, data=message, headers=headers), 10)
        return res.status == 202
    except asyncio.TimeoutError:
        logging.error('Request to {} took more then 5s to finish, dropping'.format(url))
    return False


def project(api_key):
    url = project_url_pattern.format(api_key=api_key)
    res = yield from aiohttp.request('get', url)
    if res.status != 200:
        text = yield from res.text()
        logger.error('request to get project info from wti failed. url: %s, status: %s, body: %s' %
                     (url, res.status, text))
        return None
    data = yield from res.json()
    project_data = data['project']

    source = project_data['source_locale']['code']
    targets = (l['code'] for l in project_data['target_locales'] if l['code'] != source)
    locales = Locales(source=source, targets=targets)

    files = project_data.get('project_files', [])
    project_name = project_data.get('name')
    project_id = project_data.get('id')

    return Project(locales=locales, files=files, name=project_name, id=project_id)
