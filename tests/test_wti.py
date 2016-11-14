from . import AsyncTestCase, read_fixture

from notifier import wti
from notifier.model import *


class TestTranslate(AsyncTestCase):
    def setUp(self):
        super().setUp()
        self.client = wti.WtiClient('dummy_key')

    def test_connection_error(self):
        self.mock_session_get.return_value = self.make_res(status=404)
        with self.assertRaises(WtiConnectionError):
            self.coro(self.client.string('dummy_id', 'dummy_locale'))

    def test_string(self):
        expected = WtiString(22683983, '#bbb\n\nbbb', 'pl')
        body = read_fixture('translation_pl.json')
        self.mock_session_get.return_value = self.make_res(body=body)
        actual = self.coro(self.client.string('dummy_id', 'dummy_locale'))
        self.assertEqual(expected, actual)

    def test_user(self):
        body = read_fixture('users.json')
        self.mock_session_get.return_value = self.make_res(body=body)
        user = self.coro(self.client.user(19362))
        self.assertEqual(user.id, 19362)
        self.assertEqual(user.email, 'test_test@gmail.com')
        self.assertEqual(user.role, WtiUserRoles.manager)

    def test_change_status(self):
        self.mock_wait.return_value = self.make_res(status=202)
        string = WtiString('dummy_id', 'dummy_text', 'dummy_locale')
        actual = self.coro(self.client.change_status(string))
        self.assertTrue(actual)

    def test_project(self):
        expected = WtiProject(9800, 'testp', 'en-US', 'activate_trial.xml', WtiContentTypes.md)
        body = read_fixture('project.json')
        self.mock_session_get.return_value = self.make_res(body=body)
        actual = self.coro(self.client.project(395411, WtiContentTypes.md))
        self.assertEqual(expected, actual)
