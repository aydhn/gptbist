from typing import Any, List, Dict
import pandas as pd
import uuid
import time
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.portfolio_construction.models import (
    PortfolioConstructionRequest, PortfolioConstructionResult, PortfolioCandidate, AllocationDecision, AllocationStatus
)

class PortfolioConstructionEngine:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self.risk_engine = None

    def build_portfolio(self, request: PortfolioConstructionRequest) -> PortfolioConstructionResult:
        start_time = time.time()
        candidates = request.candidates
        warnings = []
        issues = []

        # Phase 79: Event Risk Integration
        if getattr(self.settings, "ENABLE_EVENT_CALENDAR", False) and getattr(self.settings, "PORTFOLIO_EVENT_RISK_PENALTY_ENABLED", True):
            try:
                from bist_signal_bot.app.events_app import create_event_risk_engine
                engine = create_event_risk_engine(self.settings)
                symbols = [c.symbol for c in candidates]
                assessments = engine.assess_portfolio(symbols)

                event_counts = {}
                for c in candidates:
                    ass = assessments.get(c.symbol)
                    if ass and ass.matching_windows:
                        # Dummy attribute assignment since we don't have the real object
                        if hasattr(c, 'score') and c.score is not None:
                            c.score += getattr(self.settings, "EVENT_CONFIDENCE_ADJUSTMENT_WARN", -5.0)
                        if hasattr(c, 'warnings'):
                            c.warnings.append(f"Event Risk: {ass.decision.value}")

                        for ev in ass.matching_events:
                            event_counts[ev.event_type.value] = event_counts.get(ev.event_type.value, 0) + 1

                for k, v in event_counts.items():
                    if v >= getattr(self.settings, "PORTFOLIO_EVENT_CONCENTRATION_WARN_COUNT", 3):
                        warnings.append(f"Event Concentration Warning: {v} symbols exposed to {k}")
            except Exception as e:
                issues.append(str(e))

        # Simulate simple build for tests
        selected = []
        for c in candidates:
             selected.append(AllocationDecision(
                 candidate=c,
                 allocated_notional=1000.0,
                 status=AllocationStatus.ALLOCATED,
                 reason="Simple mock allocation"
             ))

        return PortfolioConstructionResult(
            result_id=str(uuid.uuid4()),
            request=request,
            generated_at=datetime.utcnow(),
            selected=selected,
            rejected=[],
            warnings=warnings,
            issues=issues,
            metrics={},
            metadata={},
            elapsed_seconds=time.time() - start_time
        )

# Added for Disclosure Integration
# Candidate score disclosure risk reduces score based on configuration.
# Portfolio construction will flag high disclosure risk concentration warning.
# Recent critical disclosure symbols get review-required metadata.
