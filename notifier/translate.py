import aiohttp
import asyncio
import json
from parse import parse
from functools import partial
from collections import namedtuple

translation_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/strings/{string_id}/locales/{locale}/translations.json'
user_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/users.json'
status_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/strings/{string_id}/locales/{locale}/translations'
project_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}.json'

Locales = namedtuple('Locales', ['source', 'targets'])
MasterFile = namedtuple('MasterFile', ['id', 'path'])
File = namedtuple('File', ['id', 'master_id', 'path'])


def string(api_key, locale, string_id):
    url = translation_url_pattern.format(api_key=api_key, locale=locale, string_id=string_id)
    res = yield from aiohttp.request('get', url)
    data = yield from res.json()
    return data['text']


def user(api_key, user_id):
    url = user_url_pattern.format(api_key=api_key)
    res = yield from aiohttp.request('get', url)
    users = yield from res.json()
    for user in users:
        if user['id'] == user_id:
            return user
    return {}


def change_status(api_key, locale, string_id, text, status='status_unverified'):
    message = json.dumps({
        'text': text,
        'status': status,
        'minor_change': False
    })
    url = status_url_pattern.format(api_key=api_key, locale=locale, string_id=string_id)
    res = yield from aiohttp.request('post', url, data=message)

    return res.status == 202


def files(api_key):
    url = project_url_pattern.format(api_key=api_key)
    res = yield from aiohttp.request('get', url)
    data = yield from res.json()
    project = data['project']
    locales = Locales._make([project['source_locale']['code'], map(lambda l: l['code'], project['target_locales'])])
    master_files = (MasterFile._make([f['id'], f['name']])
                                     for f in project['project_files'] if not f['master_project_file_id'])
    files = (File._make([f['id'], f['master_project_file_id'], f['name']])
                        for f in project['project_files'] if f['master_project_file_id'])
    return locales, master_files, files
