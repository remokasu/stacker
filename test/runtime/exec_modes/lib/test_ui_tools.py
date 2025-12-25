import unittest
from unittest.mock import patch, mock_open
from stacker.lib.ui_tools import disp_logo, disp_about, disp_help, delete_history


class TestUITools(unittest.TestCase):
    @patch("stacker.lib.ui_tools.files")
    @patch("stacker.lib.ui_tools.colored")
    def test_disp_logo(self, mock_colored, mock_files):
        mock_file = mock_open(read_data=b"Line1\nLine2\nLine3\nLine4\nLine5\nLine6\n")
        mock_files.return_value.joinpath.return_value.open = mock_file

        with patch("builtins.print") as mock_print:
            disp_logo()
            self.assertEqual(mock_print.call_count, 7)  # 6 lines + 1 empty line
            self.assertTrue(mock_colored.called)

    @patch("stacker.lib.ui_tools.files")
    def test_disp_about(self, mock_files):
        mock_file = mock_open(read_data=b"About message")
        mock_files.return_value.joinpath.return_value.open = mock_file

        with patch("builtins.print") as mock_print:
            disp_about()
            mock_print.assert_called_once_with("About message")

    @patch("stacker.lib.ui_tools.files")
    def test_disp_help(self, mock_files):
        mock_file = mock_open(read_data=b"Help message")
        mock_files.return_value.joinpath.return_value.open = mock_file

        with patch("builtins.print") as mock_print:
            disp_help()
            mock_print.assert_called_once_with("Help message")

    @patch("stacker.lib.ui_tools.history_file_path")
    def test_delete_history(self, mock_history_file_path):
        mock_history_file_path.exists.return_value = True

        delete_history()
        mock_history_file_path.unlink.assert_called_once()

        mock_history_file_path.exists.return_value = False
        delete_history()
        with patch.object(
            mock_history_file_path, "unlink", wraps=mock_history_file_path.unlink
        ) as mock_unlink:
            delete_history()
            mock_unlink.assert_not_called()


if __name__ == "__main__":
    unittest.main()
