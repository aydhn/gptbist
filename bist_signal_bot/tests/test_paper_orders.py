import pytest
from bist_signal_bot.paper.orders import PaperOrderManager
from bist_signal_bot.paper.models import PaperOrderSide, PaperOrderStatus, PaperAccount, PaperAccountStatus
from bist_signal_bot.strategies.models import SignalCandidate, SignalIntent
from bist_signal_bot.risk.models import RiskDecision, RiskDecisionStatus

def test_order_reject_if_account_not_active():
    # 8. Account ACTIVE değilse order reject edilir.
    manager = PaperOrderManager()
    acc = PaperAccount(account_id="a", initial_cash=100, cash=100, equity=100, status=PaperAccountStatus.PAUSED)

    order = manager.create_market_order("a", "ASELS", PaperOrderSide.BUY, 10)
    manager.validate_order_against_account(order, acc)

    assert order.status == PaperOrderStatus.REJECTED

def test_order_creates_with_metadata():
    # 13. create_market_order SignalCandidate metadata taşır.
    manager = PaperOrderManager()
    sig = SignalCandidate(symbol="ASELS", intent=SignalIntent.LONG, score=80.0, strategy_name="test")

    order = manager.create_market_order("a", "ASELS", PaperOrderSide.BUY, 10, signal=sig)
    assert order.signal_id == sig.signal_id
    assert order.strategy_name == "test"

def test_order_risk_rejection():
    # 14. RiskDecision rejected ise order rejected olur.
    manager = PaperOrderManager()
    risk = RiskDecision(symbol="ASELS", intent=SignalIntent.LONG, status=RiskDecisionStatus.REJECTED, reasons=["too risky"])

    order = manager.create_market_order("a", "ASELS", PaperOrderSide.BUY, 10, risk_decision=risk)
    assert order.status == PaperOrderStatus.REJECTED
    assert "too risky" in order.reject_reason

def test_order_accept_cancel():
    # 15. accept_order status günceller.
    # 16. cancel_order status günceller.
    manager = PaperOrderManager()
    order = manager.create_market_order("a", "ASELS", PaperOrderSide.BUY, 10)

    manager.accept_order(order)
    assert order.status == PaperOrderStatus.ACCEPTED

    manager.cancel_order(order)
    assert order.status == PaperOrderStatus.CANCELLED
