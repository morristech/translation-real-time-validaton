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
    def test_verify(self, mock_put):
        mock_res = MagicMock()
        mock_res.status = 202
        mock_put.return_value = self.make_fut(mock_res)

        actual = self.coro(translate.change_status('key', 3, 'locale', 'text'))

        self.assertTrue(actual)
        (method, url), named =  mock_put.call_args
        self.assertEqual('post', method)
        self.assertEqual('https://webtranslateit.com/api/projects/key/strings/locale/locales/3/translations', url)
        self.assertTrue('data' in named)
