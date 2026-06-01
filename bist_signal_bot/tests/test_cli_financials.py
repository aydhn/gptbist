import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from unittest.mock import patch
from bist_signal_bot.cli.commands import run_financials_command

class DummyArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def test_cli_import_dry_run(capsys):
    args = DummyArgs(financials_command="import", file="test.csv", confirm=False, dry_run=True)
    with patch('bist_signal_bot.app.financials_app.create_financial_statement_importer') as mock_importer:
        mock_inst = mock_importer.return_value
        class MockRes:
            records_imported = 0
            records_skipped = 1
            duplicate_count = 0
        mock_inst.import_file.return_value = MockRes()

        run_financials_command(args)

        captured = capsys.readouterr()
        assert "Dry run complete." in captured.out

def test_cli_ratios_json(capsys):
    args = DummyArgs(financials_command="ratios", symbol="ASELS", json=True)
    run_financials_command(args)
    captured = capsys.readouterr()
    assert '"status": "ok"' in captured.out
    assert '"command": "ratios"' in captured.out
