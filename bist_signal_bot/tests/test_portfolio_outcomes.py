from datetime import datetime, timezone
import sys
import logging

from bist_signal_bot.portfolio_ledger.models import (
    ResearchPortfolio,
    ResearchPortfolioPosition
)
from bist_signal_bot.portfolio_ledger.outcomes import PortfolioOutcomeEvaluator
from bist_signal_bot.config.settings import Settings

class MockEventRiskEngine:
    def assess_portfolio(self, symbols):
        raise ValueError("Mock error")

def test_portfolio_outcome_evaluator_exception_handling(caplog):
    # Set caplog to capture at least WARNING level messages
    caplog.set_level(logging.WARNING)

    settings = Settings(ENABLE_EVENT_CALENDAR=True)
    evaluator = PortfolioOutcomeEvaluator(settings=settings)

    portfolio = ResearchPortfolio(
        portfolio_id="test_port_1",
        name="Test Portfolio",
        status="ACTIVE_RESEARCH",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        current_simulated_nav=100.0,
        initial_notional=100.0,
        positions=[ResearchPortfolioPosition(
            position_id="pos_1",
            symbol="THYAO.IS",
            initial_price=10.0,
            current_price=10.0,
            quantity=1.0,
            target_weight=1.0,
            current_weight=1.0
        )]
    )

    # Mocking the module import that outcome evaluator uses
    class MockApp:
        @staticmethod
        def create_event_risk_engine(settings):
            return MockEventRiskEngine()

    original_app = sys.modules.get('bist_signal_bot.app.events_app')
    sys.modules['bist_signal_bot.app.events_app'] = MockApp

    try:
        result = evaluator.evaluate_outcome(portfolio)

        assert result.outcome_id is not None
        assert any("Failed to evaluate event calendar for portfolio test_port_1: Mock error" in record.message for record in caplog.records)
    finally:
        # Cleanup mock
        if original_app:
            sys.modules['bist_signal_bot.app.events_app'] = original_app
        else:
            del sys.modules['bist_signal_bot.app.events_app']
