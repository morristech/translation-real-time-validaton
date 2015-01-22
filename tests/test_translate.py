from unittest.mock import patch, MagicMock
from . import AsyncTestCase
from notifier import translate


class TestTranslate(AsyncTestCase):

    @patch('aiohttp.request')
    def test_file_happy_path(self, mock_get):
        mock_json = MagicMock()
        mock_json.json.return_value = self.make_fut({
            'text': 'test'
        })
        mock_get.return_value = self.make_fut(mock_json)

        actual = self.coro(translate.string('key', 'locale', 'id'))

        self.assertEqual('test', actual)
        mock_get.assert_called_with(
            'get', 'https://webtranslateit.com/api/projects/key/strings/id/locales/locale/translations.json')

    @patch('aiohttp.request')
    def test_user_happy_path(self, mock_get):
        mock_json = MagicMock()
        mock_json.json.return_value = self.make_fut([{'id': 1, 'name': 'test1'}, {'id': 2, 'name': 'test2'}])
        mock_get.return_value = self.make_fut(mock_json)

        actual = self.coro(translate.user('key', 2))

        self.assertEqual({'id': 2, 'name': 'test2'}, actual)

    @patch('aiohttp.request')
    def test_user_return_empty_dict_if_missing(self, mock_get):
        mock_json = MagicMock()
        mock_json.json.return_value = self.make_fut([{'id': 1, 'name': 'test1'}, {'id': 2, 'name': 'test2'}])
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

    def _test_files(self, mock_get):
        data = {
            'project': {
                'source_locale': {'code': 'en-US'},
                'target_locales': [{'code': 'en-US'}, {'code': 'pl'}],
                'project_files': [
                    {'master_project_file_id': 1, 'id': 2, 'name': 'slave_file'},
                    {'master_project_file_id': None, 'id': 1, 'name': 'master_file'}
                ]
            }
        }
        mock_res = MagicMock()
        mock_res.json.return_value = self.make_fut(data)
        mock_get.return_value = self.make_fut(mock_res)
        return self.coro(translate.files('api_kay'))

    @patch('aiohttp.request')
    def test_files_locales(self, mock_get):
        locales, _, _ = self._test_files(mock_get)

        self.assertEqual('en-US', locales.source)
        self.assertEqual(['en-US', 'pl'], list(locales.targets))

    @patch('aiohttp.request')
    def test_files_master_files(self, mock_get):
        _, master_files, _ = self._test_files(mock_get)
        master_files = list(master_files)

        self.assertEqual(1, len(master_files))
        master_file = master_files[0]

        self.assertEqual(1, master_file.id)
        self.assertEqual('master_file', master_file.path)

    @patch('aiohttp.request')
    def test_files_files(self, mock_get):
        _, _, files = self._test_files(mock_get)
        files = list(files)

        self.assertEqual(1, len(files))
        file = files[0]

        self.assertEqual(2, file.id)
        self.assertEqual(1, file.master_id)
        self.assertEqual('slave_file', file.path)
