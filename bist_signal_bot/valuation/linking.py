from datetime import datetime
from typing import List, Dict, Any, Optional

class ValuationLinker:
    def __init__(self, financials_engine: Any = None, disclosures_engine: Any = None, events_engine: Any = None, signal_store: Any = None):
        self.financials_engine = financials_engine
        self.disclosures_engine = disclosures_engine
        self.events_engine = events_engine
        self.signal_store = signal_store

    def link_to_financials(self, symbol: str, as_of: datetime) -> List[Dict[str, Any]]:
        links = []
        if self.financials_engine:
            statement = self.financials_engine.get_latest_normalized_statement(symbol, as_of)
            if statement:
                links.append({
                    "type": "FINANCIAL_STATEMENT",
                    "id": getattr(statement, "statement_id", "unknown"),
                    "description": f"Linked to financial statement ending {getattr(statement, 'period_end_date', 'unknown')}"
                })
        return links

    def link_to_disclosures(self, symbol: str, as_of: datetime) -> List[Dict[str, Any]]:
        links = []
        if self.disclosures_engine:
            # Fake/Mock call assumption based on naming
            recent_disclosures = getattr(self.disclosures_engine, "get_recent_disclosures", lambda s, a, l: [])(symbol, as_of, 3)
            for d in recent_disclosures:
                links.append({
                    "type": "DISCLOSURE",
                    "id": getattr(d, "disclosure_id", "unknown"),
                    "description": f"Recent disclosure: {getattr(d, 'title', 'unknown')}"
                })
        return links

    def link_to_events(self, symbol: str, as_of: datetime) -> List[Dict[str, Any]]:
        links = []
        if self.events_engine:
            # Fake/Mock call
            upcoming = getattr(self.events_engine, "get_upcoming_events", lambda s, a: [])(symbol, as_of)
            for e in upcoming:
                links.append({
                    "type": "CORPORATE_EVENT",
                    "id": getattr(e, "event_id", "unknown"),
                    "description": f"Upcoming event: {getattr(e, 'event_type', 'unknown')}"
                })
        return links

    def link_to_signals(self, symbol: str, as_of: datetime) -> List[Dict[str, Any]]:
        links = []
        if self.signal_store:
            # Fake/Mock call
            recent = getattr(self.signal_store, "get_recent_signals", lambda s, a: [])(symbol, as_of)
            for s in recent:
                links.append({
                    "type": "TECHNICAL_SIGNAL",
                    "id": getattr(s, "signal_id", "unknown"),
                    "description": f"Active signal: {getattr(s, 'strategy_name', 'unknown')}"
                })
        return links

    def relationship_message(self, link_type: str, symbol: str) -> str:
        return f"Research-only deterministic linking between Valuation and {link_type} for {symbol}. No investment advice."
