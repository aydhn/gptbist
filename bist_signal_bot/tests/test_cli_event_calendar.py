import sys
from unittest.mock import MagicMock
sys.modules['pandas'] = MagicMock()
sys.modules['bist_signal_bot.data.models'] = MagicMock()
import pytest
from unittest.mock import patch, MagicMock

from bist_signal_bot.cli.event_calendar_group import handle_event_calendar_command
from bist_signal_bot.config.settings import Settings

class DummyArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def test_cli_import_dry_run(tmp_path):
    csv = tmp_path / "test.csv"
    csv.write_text("event_type,scope,status,title,symbol,event_date,severity\nEARNINGS,SYMBOL,SCHEDULED,Earnings,ASELS,2024-05-01T00:00:00,HIGH")
    args = DummyArgs(event_cmd="import", file=str(csv), dry_run=True, confirm=False)

    with patch("bist_signal_bot.cli.event_calendar_group.get_settings") as mock_settings:
        mock_settings.return_value = Settings(EVENTS_DIR_NAME="test_events")
        handle_event_calendar_command(args)

def test_cli_list_upcoming():
    args = DummyArgs(event_cmd="upcoming", days=30, symbol=None, json=False)
    with patch("bist_signal_bot.cli.event_calendar_group.get_settings") as mock_settings:
        mock_settings.return_value = Settings(EVENTS_DIR_NAME="test_events")
        handle_event_calendar_command(args)

def test_cli_snapshot():
    args = DummyArgs(event_cmd="snapshot", json=False)
    with patch("bist_signal_bot.cli.event_calendar_group.get_settings") as mock_settings:
        mock_settings.return_value = Settings(EVENTS_DIR_NAME="test_events")
        handle_event_calendar_command(args)
