import uuid
from typing import Any

from bist_signal_bot.events.models import (
    BlackoutPolicy, MarketEventType, EventSeverity, EventRiskDecision, MarketEventScope, MarketEvent, EventWindow, EventWindowType
)

class BlackoutPolicyManager:
    def default_policies(self) -> list[BlackoutPolicy]:
        return [
            BlackoutPolicy(
                policy_id="default_earnings_policy",
                name="Earnings Pre/Post Window",
                event_types=[MarketEventType.EARNINGS, MarketEventType.FINANCIAL_STATEMENT],
                pre_event_days=3,
                post_event_days=2,
                severity_threshold=EventSeverity.MEDIUM,
                decision=EventRiskDecision.WARN,
                applies_to_scope=[MarketEventScope.SYMBOL]
            ),
            BlackoutPolicy(
                policy_id="default_macro_policy",
                name="Macro Event Market-Wide",
                event_types=[MarketEventType.MACRO_DATA, MarketEventType.CENTRAL_BANK, MarketEventType.INFLATION_DATA, MarketEventType.INTEREST_RATE_DECISION],
                pre_event_days=1,
                post_event_days=1,
                severity_threshold=EventSeverity.HIGH,
                decision=EventRiskDecision.REQUIRE_REVIEW,
                applies_to_scope=[MarketEventScope.MARKET, MarketEventScope.MACRO]
            ),
            BlackoutPolicy(
                policy_id="default_halt_policy",
                name="Trading Halt Critical",
                event_types=[MarketEventType.TRADING_HALT],
                pre_event_days=0,
                post_event_days=0,
                severity_threshold=EventSeverity.CRITICAL,
                decision=EventRiskDecision.RESEARCH_BLOCK,
                applies_to_scope=[MarketEventScope.SYMBOL]
            )
        ]

    def get_policy(self, policy_id_or_name: str) -> BlackoutPolicy | None:
        for p in self.default_policies():
            if p.policy_id == policy_id_or_name or p.name == policy_id_or_name:
                return p
        return None

    def evaluate_policy(self, event: MarketEvent, policy: BlackoutPolicy) -> EventWindow | None:
        if event.event_type not in policy.event_types:
            return None

        if not policy.enabled:
            return None

        return EventWindow(
            window_id=str(uuid.uuid4()),
            event_id=event.event_id,
            window_type=EventWindowType.BLACKOUT,
            starts_at=event.event_date, # simplified
            ends_at=event.event_date, # simplified
            severity=policy.severity_threshold,
            decision=policy.decision,
            reason=f"Matched policy {policy.name}"
        )

    def should_research_block(self, assessment: Any) -> bool:
        return assessment.decision == EventRiskDecision.RESEARCH_BLOCK

    def validate_policy(self, policy: BlackoutPolicy) -> list[str]:
        errors = []
        if policy.pre_event_days < 0 or policy.post_event_days < 0:
            errors.append("Pre and post event days must be >= 0")
        return errors
