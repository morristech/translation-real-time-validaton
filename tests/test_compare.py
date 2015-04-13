from unittest.mock import patch
from . import AsyncTestCase
from notifier import compare

class TestCompare(AsyncTestCase):
    def test_diff_happy_path(self):
        actual = self.coro(compare.diff('aaa', 'aaa'))
        self.assertEqual('', actual)

    def test_diff_same_structure(self):
        actual = self.coro(compare.diff('''##Tiempo de espera del PIN
¿Entra y sale de KeepSafe con frecuencia? [Esta opción premium hace que esto sea más seguro y rápido](http://support.getkeepsafe.com/hc/articles/204056310).

Active el Tiempo de espera del PIN y así KeepSafe se mantendrá desbloqueado durante 30 segundos después de que salga de la aplicación. Si vuelve antes de transcurrido ese tiempo, no tendrá que ingresar nuevamente el PIN.
''', '''##PIN timeout
Do you go in and out of KeepSafe frequently? [Premium makes this safer and faster](http://support.getkeepsafe.com/hc/articles/204056310).

Activate PIN timeout and KeepSafe stays unlocked for 30 seconds after you leave the app. If you come back within that time, you won’t have to enter your PIN.
'''))
        self.assertEqual('', actual)

    def test_diff_different_structure(self):
        actual = self.coro(compare.diff('##aaa\n\naaa', '#bbb\n\nbbb'))
        self.assertNotEqual('', actual)
