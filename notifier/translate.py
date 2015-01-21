import aiohttp
from parse import parse

translation_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/strings/{string_id}.json?filters[locale]={locale}'
user_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/users.json'
string_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/strings/{string_id}.json'


def string(api_key, locale, string_id):
    url = translation_url_pattern.format(api_key=api_key, locale=locale, string_id=string_id)
    res = yield from aiohttp.request('get', url)
    data = yield from res.json()
    return data['translations']['text']


def user(api_key, user_id):
    url = user_url_pattern.format(api_key=api_key)
    res = yield from aiohttp.request('get', url)
    users = yield from res.json()
    for user in users:
        if user['id'] == user_id:
            return user
    return {}


def change_status(api_key, string_id, status='status_unverified'):
    message = {
        'status': status
    }
    url = string_url_pattern.format(api_key=api_key, string_id=string_id)
    res = yield from aiohttp.request('put', url)
    return res.status == 202
