from datetime import datetime
from typing import List, Optional
import uuid
import re
from bist_signal_bot.markets.models import MarketGovernanceAssessment, MarketStatus, MarketDefinition
from bist_signal_bot.markets.registry import MarketRegistry
from bist_signal_bot.markets.instruments import InstrumentRegistry
from bist_signal_bot.markets.calendar import MarketCalendarProvider

class MarketGovernanceEngine:
    def __init__(self, market_registry: MarketRegistry, instrument_registry: InstrumentRegistry, calendar_provider: MarketCalendarProvider, store=None):
        self.market_registry = market_registry
        self.instrument_registry = instrument_registry
        self.calendar_provider = calendar_provider
        self.store = store

    def registry_complete(self, market: Optional[MarketDefinition]) -> bool:
        return market is not None

    def calendar_available(self, market_id: str) -> bool:
        # Simple mock check
        return True

    def instruments_available(self, market_id: str) -> bool:
        return len(self.instrument_registry.list_instruments(market_id)) > 0

    def currency_valid(self, market: Optional[MarketDefinition]) -> bool:
        if not market: return False
        return len(market.default_currency) == 3

    def unsafe_language_findings(self, text: str) -> List[str]:
        unsafe = ["trade ready", "işlem yapılabilir", "al/sat", "hedef fiyat", "live ready", "market open guaranteed", "tradable", "guarantee", "investment advice"]
        findings = []
        text_lower = text.lower()
        for u in unsafe:
            if u in text_lower:
                findings.append(f"Unsafe claim found: {u}")
        return findings

    def status_from_parts(self, parts: dict[str, bool], unsafe: List[str]) -> MarketStatus:
        if unsafe:
            return MarketStatus.BLOCKED
        if not parts.get('registry_complete'):
            return MarketStatus.FAIL
        if not parts.get('instruments_available') or not parts.get('calendar_available'):
            return MarketStatus.WATCH
        return MarketStatus.ACTIVE

    def assess_market(self, market_id: str) -> MarketGovernanceAssessment:
        market = self.market_registry.get_market(market_id)

        parts = {
            'registry_complete': self.registry_complete(market),
            'calendar_available': self.calendar_available(market_id),
            'instruments_available': self.instruments_available(market_id),
            'currency_valid': self.currency_valid(market)
        }

        # Check market definition text for unsafe claims
        unsafe = []
        if market:
            unsafe.extend(self.unsafe_language_findings(market.name))
            if market.metadata:
                unsafe.extend(self.unsafe_language_findings(str(market.metadata)))

        status = self.status_from_parts(parts, unsafe)

        ass = MarketGovernanceAssessment(
            assessment_id=str(uuid.uuid4()),
            market_id=market_id,
            created_at=datetime.now(),
            status=status,
            registry_complete=parts['registry_complete'],
            calendar_available=parts['calendar_available'],
            instruments_available=parts['instruments_available'],
            currency_valid=parts['currency_valid'],
            unsafe_language_findings=unsafe,
            caveats=["Governance trade permission değildir."]
        )

        if self.store:
            self.store.append_governance(ass)

        return ass
