from datetime import datetime, timezone
from bist_signal_bot.valuation.linking import ValuationLinker

def test_valuation_linking_disclaimer():
    linker = ValuationLinker()
    msg = linker.relationship_message("FINANCIAL_STATEMENT", "TEST")
    assert "No investment advice" in msg
    assert "deterministic linking" in msg
