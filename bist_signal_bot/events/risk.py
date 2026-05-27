from datetime import datetime
import uuid
from typing import Any

from bist_signal_bot.events.models import (
    MarketEvent, EventWindow, EventRiskAssessment, EventRiskDecision, EventSeverity
)

class EventRiskEngine:
    def __init__(self, calendar=None, window_builder=None, policy_manager=None):
        self.calendar = calendar
        self.window_builder = window_builder
        self.policy_manager = policy_manager

    def assess_symbol(self, symbol: str, strategy_name: str | None = None, signal_id: str | None = None, as_of: datetime | None = None) -> EventRiskAssessment:
        as_of = as_of or datetime.now()

        events = []
        if self.calendar:
            events = self.calendar.events_for_symbol(symbol, as_of)
            events.extend([ev for ev in self.calendar.list_events() if ev.scope in ["MARKET", "MACRO"] and abs((ev.event_date - as_of).days) <= 10])

        policies = None
        if self.policy_manager:
            policies = self.policy_manager.default_policies()

        windows = []
        if self.window_builder:
            all_windows = self.window_builder.build_windows(events, policies)
            windows = self.window_builder.active_windows(as_of, all_windows, symbol=symbol)

        score = self.risk_score(events, windows)
        severity = EventSeverity.LOW

        if windows:
            severity = max([w.severity for w in windows], key=lambda x: list(EventSeverity).index(x))

        decision = self.decision_from_score(score, severity)
        adj = self.confidence_adjustment(decision, score)

        blocking = []
        if decision == EventRiskDecision.RESEARCH_BLOCK:
            blocking.append("High event risk active window")

        return EventRiskAssessment(
            assessment_id=str(uuid.uuid4()),
            symbol=symbol,
            strategy_name=strategy_name,
            signal_id=signal_id,
            assessed_at=as_of,
            matching_events=events,
            matching_windows=windows,
            risk_score=score,
            severity=severity,
            decision=decision,
            confidence_adjustment=adj,
            blocking_reasons=blocking
        )

    def assess_signal(self, signal_payload: dict[str, Any], as_of: datetime | None = None) -> EventRiskAssessment:
        return self.assess_symbol(
            symbol=signal_payload.get('symbol', ''),
            strategy_name=signal_payload.get('strategy_name'),
            signal_id=signal_payload.get('signal_id'),
            as_of=as_of
        )

    def assess_portfolio(self, symbols: list[str], as_of: datetime | None = None) -> dict[str, EventRiskAssessment]:
        results = {}
        for sym in symbols:
            results[sym] = self.assess_symbol(sym, as_of=as_of)
        return results

    def risk_score(self, events: list[MarketEvent], windows: list[EventWindow]) -> float | None:
        if not windows:
            return 0.0

        score = 0.0
        for w in windows:
            if w.severity == EventSeverity.CRITICAL:
                score += 50
            elif w.severity == EventSeverity.HIGH:
                score += 30
            elif w.severity == EventSeverity.MEDIUM:
                score += 15
            else:
                score += 5

        return min(100.0, score)

    def decision_from_score(self, score: float | None, severity: EventSeverity) -> EventRiskDecision:
        if score is None or score == 0:
            return EventRiskDecision.ALLOW

        if severity == EventSeverity.CRITICAL and score > 80:
            return EventRiskDecision.RESEARCH_BLOCK

        if score > 65:
            return EventRiskDecision.REQUIRE_REVIEW

        if score > 40:
            return EventRiskDecision.WARN

        return EventRiskDecision.WATCH

    def confidence_adjustment(self, decision: EventRiskDecision, score: float | None) -> float | None:
        if decision == EventRiskDecision.RESEARCH_BLOCK:
            return -20.0
        elif decision == EventRiskDecision.REQUIRE_REVIEW:
            return -10.0
        elif decision == EventRiskDecision.WARN:
            return -5.0
        return 0.0

# Added for Disclosure Integration
# EventRiskAssessment carries matching disclosures metadata
