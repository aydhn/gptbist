import uuid
from datetime import datetime, UTC
from typing import Optional

from bist_signal_bot.core.exceptions import PaperOrderError
from bist_signal_bot.paper.models import (
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


class PaperOrderManager:

    def create_market_order(
        self,
        account_id: str,
        symbol: str,
        side: PaperOrderSide,
        quantity: float,
        requested_price: Optional[float] = None,
        signal: Optional[SignalCandidate] = None,
        risk_decision: Optional[RiskDecision] = None,
        portfolio_decision: Optional[PortfolioRiskDecision] = None
    ) -> PaperOrder:
        if quantity <= 0:
            raise PaperOrderError("Order quantity must be positive")

        order_id = str(uuid.uuid4())

        status = PaperOrderStatus.CREATED
        reject_reason = None

        if risk_decision and risk_decision.status.value != "APPROVED":
             status = PaperOrderStatus.REJECTED
             reject_reason = f"Risk rejected: {risk_decision.reasons[0] if risk_decision.reasons else 'No reason provided'}"

        if portfolio_decision and portfolio_decision.status.value != "APPROVED":
             status = PaperOrderStatus.REJECTED
             reject_reason = f"Portfolio Risk rejected: {portfolio_decision.reasons[0] if portfolio_decision.reasons else 'No reason provided'}"

        order = PaperOrder(
            order_id=order_id,
            account_id=account_id,
            symbol=symbol.upper(),
            side=side,
            order_type=PaperOrderType.MARKET,
            status=status,
            quantity=quantity,
            requested_price=requested_price,
            signal_id=signal.signal_id if signal else None,
            strategy_name=signal.strategy_name if signal else None,
            risk_decision_summary=risk_decision.model_dump() if risk_decision else {},
            portfolio_decision_summary=portfolio_decision.model_dump() if portfolio_decision else {},
            reject_reason=reject_reason
        )

        return order

    def accept_order(self, order: PaperOrder) -> PaperOrder:
        if order.status not in [PaperOrderStatus.CREATED, PaperOrderStatus.REJECTED]:
             raise PaperOrderError(f"Cannot accept order in status {order.status}")

        order.status = PaperOrderStatus.ACCEPTED
        order.updated_at = datetime.now(UTC)
        return order

    def reject_order(self, order: PaperOrder, reason: str) -> PaperOrder:
        if order.status in [PaperOrderStatus.FILLED, PaperOrderStatus.CANCELLED, PaperOrderStatus.EXPIRED]:
             raise PaperOrderError(f"Cannot reject order in status {order.status}")

        order.status = PaperOrderStatus.REJECTED
        order.reject_reason = reason
        order.updated_at = datetime.now(UTC)
        return order

    def cancel_order(self, order: PaperOrder, reason: Optional[str] = None) -> PaperOrder:
        if order.status in [PaperOrderStatus.FILLED, PaperOrderStatus.CANCELLED, PaperOrderStatus.EXPIRED, PaperOrderStatus.REJECTED]:
             raise PaperOrderError(f"Cannot cancel order in status {order.status}")

        order.status = PaperOrderStatus.CANCELLED
        if reason:
             order.reject_reason = reason
        order.updated_at = datetime.now(UTC)
        return order

    def expire_order(self, order: PaperOrder) -> PaperOrder:
        if order.status in [PaperOrderStatus.FILLED, PaperOrderStatus.CANCELLED, PaperOrderStatus.EXPIRED, PaperOrderStatus.REJECTED]:
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
