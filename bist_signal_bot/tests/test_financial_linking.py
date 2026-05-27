import pytest
from bist_signal_bot.financials.linking import FinancialLinker

def test_financial_linking():
    linker = FinancialLinker()
    assert linker.relationship_message("disclosure", "ASELS") == "Linked disclosure for ASELS"
