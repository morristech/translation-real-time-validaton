import aiohttp
from parse import parse

file_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/files/{file_id}/locales/{locale}'
user_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/users.json'


def get_wti_key(url):
    return parse(file_url_pattern, url).named['api_key']


def file(api_key, locale, file_id):
    url = file_url_pattern.format(api_key=api_key, locale=locale, file_id=file_id)
    res = aiohttp.request('get', url)
    return (yield from res.text())


def master(api_key, locale, url):
    args = parse(file_url_pattern, url).named
    return (yield from file(api_key, locale, args['file_id']))


def user(api_key, user_id):
    url = user_url_pattern.format(api_key=api_key)
    res = aiohttp.request('get', url)
    users = yield from res.json()
    for user in users:
        if user['id'] == user_id:
            return user
    return {}
