import aiohttp
from parse import parse

file_url_pattern = 'https://webtranslateit.com/api/projects/{api_key}/files/{file_id}/locales/{locale}'


def file(api_key, locale, file_id):
    url = file_url_pattern.format(api_key=api_key, locale=locale, file_id=file_id)
    res = aiohttp.request('get', url)
    yield from res.text()

def master(locale, url):
    args = parse(file_url_pattern, url).named
    yield from file(args['api_key'], locale, args['file_id'])
