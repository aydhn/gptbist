from datetime import datetime, timezone
import uuid
from typing import Any

from bist_signal_bot.portfolio_ledger.models import (
    ResearchPortfolio,
    ResearchPortfolioStatus,
    PortfolioLedgerEvent,
    PortfolioLedgerEventType,
    ResearchPortfolioPosition
)
from bist_signal_bot.core.exceptions import PortfolioLedgerError

class ResearchPortfolioLedger:
    def __init__(self, store: Any):
        self.store = store

    def create_portfolio(
        self,
        name: str,
        construction_result: Any | None = None,
        initial_notional: float | None = None,
        confirm: bool = False
    ) -> ResearchPortfolio:
        if not confirm:
            raise PortfolioLedgerError("Creating a portfolio requires confirmation (confirm=True).")

        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc)

        initial_notional = initial_notional or 100000.0

        portfolio = ResearchPortfolio(
            portfolio_id=portfolio_id,
            name=name,
            status=ResearchPortfolioStatus.DRAFT,
            created_at=now,
            updated_at=now,
            construction_result_id=getattr(construction_result, "result_id", None) if construction_result else None,
            initial_notional=initial_notional,
            positions=[]
        )

        self.store.append_portfolio(portfolio)

        event = PortfolioLedgerEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            portfolio_id=portfolio_id,
            event_type=PortfolioLedgerEventType.CREATED,
            created_at=now,
            message="Portfolio created.",
            new_status=ResearchPortfolioStatus.DRAFT
        )
        self.append_event(event)

        return portfolio

    def create_from_construction_result(
        self,
        result: Any,
        name: str | None = None,
        confirm: bool = False
    ) -> ResearchPortfolio:
        if not confirm:
            raise PortfolioLedgerError("Creating a portfolio requires confirmation (confirm=True).")

        portfolio_name = name or f"Portfolio from {getattr(result, 'result_id', 'unknown')}"
        portfolio = self.create_portfolio(name=portfolio_name, construction_result=result, confirm=confirm)

        positions = []
        if hasattr(result, "allocations"):
            for alloc in result.allocations:
                # Mapping generic allocations to research positions
                positions.append(
                    ResearchPortfolioPosition(
                        position_id=f"pos_{uuid.uuid4().hex[:8]}",
                        symbol=alloc.symbol,
                        target_weight=alloc.weight,
                        current_weight=alloc.weight, # Initially assume it hits target exactly for simulation
                        latest_price=getattr(alloc, "price", None),
                        entry_research_price=getattr(alloc, "price", None)
                    )
                )

        portfolio.positions = positions
        portfolio.updated_at = datetime.now(timezone.utc)

        # We append a new version to the store, since it's append-only we re-save the updated portfolio.
        self.store.append_portfolio(portfolio)

        event = PortfolioLedgerEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            portfolio_id=portfolio.portfolio_id,
            event_type=PortfolioLedgerEventType.UPDATED,
            created_at=portfolio.updated_at,
            message="Positions populated from construction result."
        )
        self.append_event(event)

        return portfolio

    def get_portfolio(self, portfolio_id_or_name: str) -> ResearchPortfolio | None:
        return self.store.get_portfolio(portfolio_id_or_name)

    def list_portfolios(self, status: ResearchPortfolioStatus | None = None, limit: int = 100) -> list[ResearchPortfolio]:
        return self.store.load_portfolios(status=status, limit=limit)

    def update_portfolio(self, portfolio: ResearchPortfolio, reason: str, confirm: bool = False) -> ResearchPortfolio:
        if not confirm:
            raise PortfolioLedgerError("Updating a portfolio requires confirmation (confirm=True).")

        portfolio.updated_at = datetime.now(timezone.utc)
        self.store.append_portfolio(portfolio)

        event = PortfolioLedgerEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            portfolio_id=portfolio.portfolio_id,
            event_type=PortfolioLedgerEventType.UPDATED,
            created_at=portfolio.updated_at,
            message=f"Portfolio updated: {reason}"
        )
        self.append_event(event)

        return portfolio

    def append_event(self, event: PortfolioLedgerEvent) -> PortfolioLedgerEvent:
        self.store.append_event(event)
        return event

    def close_portfolio(self, portfolio_id: str, reason: str, confirm: bool = False) -> PortfolioLedgerEvent:
        if not confirm:
            raise PortfolioLedgerError("Closing a portfolio requires confirmation (confirm=True).")

        portfolio = self.get_portfolio(portfolio_id)
        if not portfolio:
            raise PortfolioLedgerError(f"Portfolio not found: {portfolio_id}")

        prev_status = portfolio.status
        portfolio.status = ResearchPortfolioStatus.CLOSED
        portfolio.updated_at = datetime.now(timezone.utc)

        self.store.append_portfolio(portfolio)

        event = PortfolioLedgerEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            portfolio_id=portfolio_id,
            event_type=PortfolioLedgerEventType.CLOSED,
            created_at=portfolio.updated_at,
            message=f"Portfolio closed: {reason}",
            previous_status=prev_status,
            new_status=ResearchPortfolioStatus.CLOSED
        )
        self.append_event(event)

        return event
