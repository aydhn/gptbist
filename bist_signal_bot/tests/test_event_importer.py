import pytest
from datetime import datetime
from pathlib import Path

from bist_signal_bot.events.importer import EventImporter
from bist_signal_bot.events.calendar import EventCalendar

def test_importer_invalid_file(tmp_path):
    importer = EventImporter()
    with pytest.raises(FileNotFoundError):
        importer.import_file(tmp_path / "missing.csv")

def test_importer_json(tmp_path):
    json_file = tmp_path / "events.json"
    json_file.write_text("""
    [
        {
            "event_type": "EARNINGS",
            "scope": "SYMBOL",
            "status": "SCHEDULED",
            "title": "GARAN Earnings",
            "symbol": "GARAN",
            "event_date": "2024-05-01T00:00:00",
            "severity": "HIGH",
            "source": "JSON_TEST"
        }
    ]
    """)

    calendar = EventCalendar()
    importer = EventImporter(calendar=calendar)

    res = importer.import_file(json_file, confirm=True)
    assert res.events_imported == 1

    ev = calendar.list_events(symbol="GARAN")
    assert len(ev) == 1
    assert ev[0].title == "GARAN Earnings"
