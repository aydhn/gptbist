import pytest
from bist_signal_bot.disclosures.reporting import format_disclosure_report_markdown, disclosure_to_dict
from bist_signal_bot.disclosures.models import DisclosureRecord, DisclosureType
from datetime import datetime

def test_disclosure_reporting_markdown():
    record = DisclosureRecord(disclosure_id="1", title="Test", body="Test", disclosure_type=DisclosureType.MATERIAL_EVENT, received_at=datetime.now(), source="test", language="tr")
    markdown = format_disclosure_report_markdown([record], [], [])
    assert "not investment advice" in markdown

def test_disclosure_reporting_dict():
    record = DisclosureRecord(disclosure_id="1", title="Test", body="Test", disclosure_type=DisclosureType.MATERIAL_EVENT, received_at=datetime.now(), source="test", language="tr")
    d = disclosure_to_dict(record)
    assert d["disclosure_id"] == "1"
    assert d["title"] == "Test"
