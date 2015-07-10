from unittest.mock import patch, MagicMock
from . import AsyncTestCase
from notifier import translate


class TestTranslate(AsyncTestCase):

    @patch('aiohttp.request')
    def test_string_happy_path(self, mock_get):
        mock_json = MagicMock()
        mock_json.json.return_value = self.make_fut({
            'text': 'test'
        })
        mock_get.return_value = self.make_fut(mock_json)

        actual = self.coro(translate.string('key', 'locale', 'id'))

        self.assertEqual(translate.Translation(id='id', locale='locale', text='test'), actual)

    @patch('aiohttp.request')
    def test_strings_happy_path(self, mock_get):
        data = [{'id': 1, 'file': {'id': 2}}]
        mock_res = MagicMock()
        mock_res.json.return_value = self.make_fut(data)
        mock_get.return_value = self.make_fut(mock_res)

        strings = list(self.coro(translate.strings('api_kay')))

        self.assertEqual(1, len(strings))
        actual = strings[0]
        self.assertEqual(1, actual.id)
        self.assertEqual(2, actual.file_id)

    @patch('aiohttp.request')
    def test_user_happy_path(self, mock_get):
        mock_json = MagicMock()
        mock_json.json.return_value = self.make_fut([{'user_id': 1, 'name': 'test1'}, {'user_id': 2, 'name': 'test2'}])
        mock_get.return_value = self.make_fut(mock_json)

        actual = self.coro(translate.user('key', 2))

        self.assertEqual({'user_id': 2, 'name': 'test2'}, actual)

    @patch('aiohttp.request')
    def test_user_return_empty_dict_if_missing(self, mock_get):
        mock_json = MagicMock()
        mock_json.json.return_value = self.make_fut([{'user_id': 1, 'name': 'test1'}, {'user_id': 2, 'name': 'test2'}])
        mock_get.return_value = self.make_fut(mock_json)

        actual = self.coro(translate.user('key', 3))

        self.assertEqual({}, actual)

    @patch('aiohttp.request')
    def test_change_status_happy_path(self, mock_put):
        mock_res = MagicMock()
        mock_res.status = 202
        mock_put.return_value = self.make_fut(mock_res)

        actual = self.coro(translate.change_status('key', 3, 'locale', 'text'))

        self.assertTrue(actual)
        (method, url), named = mock_put.call_args
        self.assertEqual('post', method)
        self.assertEqual('https://webtranslateit.com/api/projects/key/strings/locale/locales/3/translations', url)
        self.assertTrue('data' in named)

    def _test_project(self, mock_get, res_status=200):
        data = {
            'project': {
                'source_locale': {'code': 'en-US'},
                'target_locales': [{'code': 'en-US'},{'code': 'pl'}],
                'project_files': [{'id': 1}]
            }
        }
        mock_res = MagicMock()
        mock_res.status = res_status
        mock_res.json.return_value = self.make_fut(data)
        mock_get.return_value = self.make_fut(mock_res)

        return self.coro(translate.project('api_kay'))

    @patch('aiohttp.request')
    def test_project_locales(self, mock_get):
        project = self._test_project(mock_get)
        locales = project.locales

        self.assertEqual('en-US', locales.source)
        self.assertEqual(['pl'], list(locales.targets))

    @patch('aiohttp.request')
    def test_project_files(self, mock_get):
        project = self._test_project(mock_get)
        files = project.files

        self.assertEqual([{'id':1}], files)

    @patch('aiohttp.request')
    def test_project_failed_request(self, mock_get):
        actual = self._test_project(mock_get, 404)
        self.assertIsNone(actual)
