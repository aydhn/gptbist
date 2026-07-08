import sys
import subprocess
from unittest.mock import patch

import pytest

from bist_signal_bot.main import main


def test_main():
    """Test that main() delegates to run_cli()."""
    with patch("bist_signal_bot.main.run_cli") as mock_run_cli:
        mock_run_cli.return_value = 0

        result = main()

        mock_run_cli.assert_called_once()
        assert result == 0


def test_main_script_execution():
    """Test the __name__ == '__main__' block execution."""
    # Running the script in a subprocess to cleanly test the __main__ block execution.
    # We pass the --help flag to trigger a clean exit from run_cli() without needing configuration.
    result = subprocess.run(
        [sys.executable, "-m", "bist_signal_bot.main", "--help"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0
    assert "usage:" in result.stdout.lower()
