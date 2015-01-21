import aiohttp
from parse import parse

translation_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/strings/{string_id}/locales/{locale}/translations.json'
user_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/users.json'
status_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/strings/{string_id}/locales/{locale}/translations'


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
    message = {
        'text': text,
        'status': status,
        'minor_change': False
    }
    url = status_url_pattern.format(api_key=api_key, locale=locale, string_id=string_id)
    res = yield from aiohttp.request('post', url, data=message)
    return res.status == 202
