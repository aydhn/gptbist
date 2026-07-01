import pytest
from datetime import datetime
from bist_signal_bot.docs_hub.models import DocsHubReport
from bist_signal_bot.docs_hub.reporting import format_docs_hub_report_markdown

def test_format_docs_hub_report_markdown():
    report = DocsHubReport(
        report_id="1",
        generated_at=datetime(2023, 10, 27, 10, 0, 0),
        key_findings=["Test finding 1", "Test finding 2"],
        disclaimer="Test disclaimer"
    )
    result = format_docs_hub_report_markdown(report)
    expected = """# Documentation Hub Report (2023-10-27 10:00:00)

## Key Findings
- Test finding 1
- Test finding 2

---
_Test disclaimer_"""
    assert result == expected


def test_format_docs_hub_report_markdown_empty_findings():
    report = DocsHubReport(
        report_id="2",
        generated_at=datetime(2023, 10, 27, 10, 0, 0),
        key_findings=[]
    )
    result = format_docs_hub_report_markdown(report)
    expected = """# Documentation Hub Report (2023-10-27 10:00:00)

## Key Findings

---
_Documentation Hub report is local software metadata only. It is not investment advice or a trading instruction. No real order was sent._"""
    assert result == expected

def test_format_docs_hub_report_markdown_default_disclaimer():
    report = DocsHubReport(
        report_id="3",
        generated_at=datetime(2023, 10, 27, 10, 0, 0),
        key_findings=["Single finding"]
    )
    result = format_docs_hub_report_markdown(report)
    expected = """# Documentation Hub Report (2023-10-27 10:00:00)

## Key Findings
- Single finding

---
_Documentation Hub report is local software metadata only. It is not investment advice or a trading instruction. No real order was sent._"""
    assert result == expected
