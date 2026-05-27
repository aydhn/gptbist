import pytest
from bist_signal_bot.financials.linking import FinancialLinker

def test_disclosure_impact_financial_statement_link():
    linker = FinancialLinker()
    assert linker.link_to_disclosures(None) == []

def test_event_calendar_financial_statement_link():
    linker = FinancialLinker()
    assert linker.link_to_events(None) == []
