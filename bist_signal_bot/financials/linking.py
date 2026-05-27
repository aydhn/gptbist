from datetime import datetime
from typing import Any
from bist_signal_bot.financials.models import NormalizedFinancialStatement

class FinancialLinker:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def link_to_disclosures(self, statement: NormalizedFinancialStatement) -> list[dict[str, Any]]:
        return []

    def link_to_events(self, statement: NormalizedFinancialStatement) -> list[dict[str, Any]]:
        return []

    def link_to_signals(self, symbol: str, period_end: datetime, lookahead_days: int = 10) -> list[dict[str, Any]]:
        return []

    def relationship_message(self, link_type: str, symbol: str) -> str:
        return f"Linked {link_type} for {symbol}"
