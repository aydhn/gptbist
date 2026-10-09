import uuid
from datetime import datetime, UTC
from typing import Optional

from bist_signal_bot.core.exceptions import PaperOrderError
from bist_signal_bot.paper.models import (
    CreateMarketOrderRequest,
    PaperAccount,
    PaperAccountStatus,
    PaperOrder,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType
)
from bist_signal_bot.strategies.models import SignalCandidate
from bist_signal_bot.risk.models import RiskDecision
from bist_signal_bot.portfolio.models import PortfolioRiskDecision


_ACCEPTABLE_STATUSES = frozenset({PaperOrderStatus.CREATED, PaperOrderStatus.REJECTED})
_REJECTABLE_STATUSES = frozenset({PaperOrderStatus.FILLED, PaperOrderStatus.CANCELLED, PaperOrderStatus.EXPIRED})
_TERMINAL_STATUSES = frozenset({PaperOrderStatus.FILLED, PaperOrderStatus.CANCELLED, PaperOrderStatus.EXPIRED, PaperOrderStatus.REJECTED})

def _summ(d):
    """JSON-safe summary of a risk/portfolio decision (pydantic model or dataclass)."""
    if d is None:
        return {}
    if hasattr(d, "summary"):
        try:
            return dict(d.summary())
        except Exception:
            pass
    if hasattr(d, "model_dump"):
        return d.model_dump()
    return {"status": str(getattr(getattr(d, "status", None), "value", getattr(d, "status", "")))}


class PaperOrderManager:

    def create_market_order(
        self,
        request: CreateMarketOrderRequest
    ) -> PaperOrder:
        if request.quantity <= 0:
            raise PaperOrderError("Order quantity must be positive")

        order_id = str(uuid.uuid4())

        status = PaperOrderStatus.CREATED
        reject_reason = None

        if request.risk_decision and request.risk_decision.status.value not in ("APPROVED", "REDUCED"):
             status = PaperOrderStatus.REJECTED
             reject_reason = f"Risk rejected: {request.risk_decision.issues[0] if getattr(request.risk_decision, 'issues', None) else 'No reason provided'}"

        if request.portfolio_decision and request.portfolio_decision.status.value not in ("APPROVED", "REDUCED", "PARTIALLY_APPROVED"):
             status = PaperOrderStatus.REJECTED
             reject_reason = f"Portfolio Risk rejected: {(str(getattr(request.portfolio_decision, 'reject_reasons', None) or getattr(request.portfolio_decision, 'warnings', None) or ['x'][:0])[:200]) if (getattr(request.portfolio_decision, 'reject_reasons', None) or getattr(request.portfolio_decision, 'warnings', None)) else 'No reason provided'}"

        order = PaperOrder(
            order_id=order_id,
            account_id=request.account_id,
            symbol=request.symbol.upper(),
            side=request.side,
            order_type=PaperOrderType.MARKET,
            status=status,
            quantity=request.quantity,
            requested_price=request.requested_price,
            signal_id=getattr(request.signal, "signal_id", None),
            strategy_name=request.signal.strategy_name if request.signal else None,
            risk_decision_summary=_summ(request.risk_decision),
            portfolio_decision_summary=_summ(request.portfolio_decision),
            reject_reason=reject_reason
        )

        return order

    def accept_order(self, order: PaperOrder) -> PaperOrder:
        if order.status not in _ACCEPTABLE_STATUSES:
             raise PaperOrderError(f"Cannot accept order in status {order.status}")

        order.status = PaperOrderStatus.ACCEPTED
        order.updated_at = datetime.now(UTC)
        return order

    def reject_order(self, order: PaperOrder, reason: str) -> PaperOrder:
        if order.status in _REJECTABLE_STATUSES:
             raise PaperOrderError(f"Cannot reject order in status {order.status}")

        order.status = PaperOrderStatus.REJECTED
        order.reject_reason = reason
        order.updated_at = datetime.now(UTC)
        return order

    def cancel_order(self, order: PaperOrder, reason: Optional[str] = None) -> PaperOrder:
        if order.status in _TERMINAL_STATUSES:
             raise PaperOrderError(f"Cannot cancel order in status {order.status}")

        order.status = PaperOrderStatus.CANCELLED
        if reason:
             order.reject_reason = reason
        order.updated_at = datetime.now(UTC)
        return order

    def expire_order(self, order: PaperOrder) -> PaperOrder:
        if order.status in _TERMINAL_STATUSES:
             raise PaperOrderError(f"Cannot expire order in status {order.status}")

        order.status = PaperOrderStatus.EXPIRED
        order.updated_at = datetime.now(UTC)
        return order

    def validate_order_against_account(self, order: PaperOrder, account: PaperAccount) -> None:
        if account.status != PaperAccountStatus.ACTIVE:
            self.reject_order(order, "Account is not ACTIVE")
            return

        # Cash/Position availability check is deferred to execution simulator
        # but we can do a preliminary check here if needed.
        pass
