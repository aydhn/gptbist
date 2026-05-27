import uuid
from typing import Any

from bist_signal_bot.events.models import MarketEvent, EventRiskAssessment, EventLink

class EventLinker:
    def link_events_to_signal(self, signal_payload: dict[str, Any], assessment: EventRiskAssessment) -> list[EventLink]:
        links = []
        for ev in assessment.matching_events:
            link = EventLink(
                link_id=str(uuid.uuid4()),
                event_id=ev.event_id,
                linked_object_type="SIGNAL",
                linked_object_id=signal_payload.get('signal_id', 'unknown'),
                symbol=assessment.symbol,
                strategy_name=assessment.strategy_name,
                relationship="active_window_during_signal",
                score=assessment.risk_score,
                message=self.relationship_message(ev, "SIGNAL")
            )
            links.append(link)
        return links

    def link_events_to_portfolio(self, portfolio_id: str, symbols: list[str], assessments: dict[str, EventRiskAssessment]) -> list[EventLink]:
        links = []
        for sym, assessment in assessments.items():
            for ev in assessment.matching_events:
                link = EventLink(
                    link_id=str(uuid.uuid4()),
                    event_id=ev.event_id,
                    linked_object_type="PORTFOLIO",
                    linked_object_id=portfolio_id,
                    symbol=sym,
                    relationship="symbol_event_exposure",
                    score=assessment.risk_score,
                    message=self.relationship_message(ev, "PORTFOLIO")
                )
                links.append(link)
        return links

    def link_events_to_backtest(self, backtest_result: Any, events: list[MarketEvent]) -> list[EventLink]:
        links = []
        backtest_id = getattr(backtest_result, 'backtest_id', 'unknown')
        for ev in events:
            link = EventLink(
                link_id=str(uuid.uuid4()),
                event_id=ev.event_id,
                linked_object_type="BACKTEST",
                linked_object_id=backtest_id,
                relationship="event_occurred_during_backtest",
                message=self.relationship_message(ev, "BACKTEST")
            )
            links.append(link)
        return links

    def link_events_to_outcomes(self, outcome_records: list[Any], events: list[MarketEvent]) -> list[EventLink]:
        # Simplified for now
        return []

    def relationship_message(self, event: MarketEvent, linked_object_type: str) -> str:
        return f"Event {event.event_type.value} relates to {linked_object_type}"

# Added for Disclosure Integration
# Support mapping disclosures metadata to linked events
