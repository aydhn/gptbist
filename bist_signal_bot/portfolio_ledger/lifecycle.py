from datetime import datetime, timezone
import uuid
from typing import Any

from bist_signal_bot.portfolio_ledger.models import (
    ResearchPortfolioStatus,
    PortfolioLedgerEvent,
    PortfolioLedgerEventType
)
from bist_signal_bot.core.exceptions import PortfolioLifecycleError

class PortfolioLifecycleManager:
    def __init__(self, store: Any):
        self.store = store

    def transition(
        self,
        portfolio_id: str,
        new_status: ResearchPortfolioStatus,
        reason: str,
        actor: str | None = None,
        confirm: bool = False
    ) -> PortfolioLedgerEvent:
        if not confirm:
            raise PortfolioLifecycleError("Transitioning requires confirmation (confirm=True).")

        portfolio = self.store.get_portfolio(portfolio_id)
        if not portfolio:
            raise PortfolioLifecycleError(f"Portfolio not found: {portfolio_id}")

        prev_status = portfolio.status
        if prev_status in (ResearchPortfolioStatus.CLOSED, ResearchPortfolioStatus.ARCHIVED):
            raise PortfolioLifecycleError(f"Cannot transition from terminal state: {prev_status}")

        portfolio.status = new_status
        portfolio.updated_at = datetime.now(timezone.utc)

        self.store.append_portfolio(portfolio)

        event_type = PortfolioLedgerEventType.UPDATED
        if new_status == ResearchPortfolioStatus.WATCH:
            event_type = PortfolioLedgerEventType.WATCH_FLAGGED
        elif new_status == ResearchPortfolioStatus.PAUSED:
            event_type = PortfolioLedgerEventType.PAUSED
        elif new_status == ResearchPortfolioStatus.CLOSED:
            event_type = PortfolioLedgerEventType.CLOSED
        elif new_status == ResearchPortfolioStatus.ARCHIVED:
            event_type = PortfolioLedgerEventType.ARCHIVED

        event = PortfolioLedgerEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            portfolio_id=portfolio_id,
            event_type=event_type,
            created_at=portfolio.updated_at,
            actor=actor,
            message=f"Status transition to {new_status}: {reason}",
            previous_status=prev_status,
            new_status=new_status
        )
        self.store.append_event(event)

        return event

    def events_for_portfolio(self, portfolio_id: str, limit: int = 100) -> list[PortfolioLedgerEvent]:
        return self.store.load_events(portfolio_id=portfolio_id, limit=limit)

    def current_status(self, portfolio_id: str) -> ResearchPortfolioStatus:
        portfolio = self.store.get_portfolio(portfolio_id)
        if not portfolio:
            raise PortfolioLifecycleError(f"Portfolio not found: {portfolio_id}")
        return portfolio.status

    def flag_watch(self, portfolio_id: str, reason: str, confirm: bool = False) -> PortfolioLedgerEvent:
        return self.transition(
            portfolio_id=portfolio_id,
            new_status=ResearchPortfolioStatus.WATCH,
            reason=reason,
            confirm=confirm
        )

    def archive(self, portfolio_id: str, reason: str, confirm: bool = False) -> PortfolioLedgerEvent:
        return self.transition(
            portfolio_id=portfolio_id,
            new_status=ResearchPortfolioStatus.ARCHIVED,
            reason=reason,
            confirm=confirm
        )
