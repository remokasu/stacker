import unittest
from unittest.mock import patch
from stacker.exec_modes.repl_mode import ReplMode
from stacker.stacker import Stacker

class TestReplMode(unittest.TestCase):
    @patch('stacker.exec_modes.repl_mode.version')
    def test_get_version(self, mock_version):
        mock_version.return_value = "1.0.0"
        rpn_calculator = Stacker()
        repl_mode = ReplMode(rpn_calculator)
        result = repl_mode.get_version()
        self.assertEqual(result, "1.0.0")
        mock_version.assert_called_once_with("pystacker")

if __name__ == '__main__':
    unittest.main()