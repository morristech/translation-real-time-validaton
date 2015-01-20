from unittest.mock import patch, MagicMock
from . import AsyncTestCase
from notifier import translate

class TestTranslate(AsyncTestCase):
    @patch('aiohttp.request')
    def test_file_happy_path(self, mock_get):
        mock_json = MagicMock()
        mock_json.text.return_value = self.make_fut('test')
        mock_get.return_value = self.make_fut(mock_json)
        actual = self.coro(translate.file('key', 'locale', 'id'))
        self.assertEqual('test', actual)
        mock_get.assert_called_with('get', 'https://webtranslateit.com/api/projects/key/files/id/locales/locale')

    @patch('aiohttp.request')
    def test_master_happy_path(self, mock_get):
        mock_json = MagicMock()
        mock_json.text.return_value = self.make_fut('test')
        mock_get.return_value = self.make_fut(mock_json)
        url = translate.file_url_pattern.format(api_key='key1', file_id='id1', locale='locale1')
        actual = self.coro(translate.master('key', 'locale', url))
        self.assertEqual('test', actual)
        mock_get.assert_called_with('get', 'https://webtranslateit.com/api/projects/key/files/id1/locales/locale')

    @patch('aiohttp.request')
    def test_user_happy_path(self, mock_get):
        mock_json = MagicMock()
        mock_json.json.return_value = self.make_fut([{'id':1, 'name':'test1'}, {'id':2, 'name':'test2'}])
        mock_get.return_value = self.make_fut(mock_json)
        actual = self.coro(translate.user('key', 2))
        self.assertEqual({'id':2, 'name': 'test2'}, actual)

    @patch('aiohttp.request')
    def test_user_return_empty_dict_if_missing(self, mock_get):
        mock_json = MagicMock()
        mock_json.json.return_value = self.make_fut([{'id':1, 'name':'test1'}, {'id':2, 'name':'test2'}])
        mock_get.return_value = self.make_fut(mock_json)
        actual = self.coro(translate.user('key', 3))
        self.assertEqual({}, actual)
