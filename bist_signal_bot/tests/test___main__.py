import sys
import subprocess
from unittest.mock import patch

from bist_signal_bot.__main__ import main

def test_main():
    """Test that main() delegates to run_cli() with sys.argv[1:]."""
    test_args = ["bist-signal-bot", "test_command", "--arg"]
    with patch("sys.argv", test_args):
        with patch("bist_signal_bot.__main__.run_cli") as mock_run_cli:
            mock_run_cli.return_value = 0

            result = main()

            mock_run_cli.assert_called_once_with(["test_command", "--arg"])
            assert result == 0

def test_main_script_execution():
    """Test the __name__ == '__main__' block execution."""
    result = subprocess.run(
        [sys.executable, "-m", "bist_signal_bot.__main__", "--help"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
