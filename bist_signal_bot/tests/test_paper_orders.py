import pytest
from bist_signal_bot.paper.orders import PaperOrderManager
from bist_signal_bot.paper.models import PaperOrderSide, PaperOrderStatus, PaperAccount, PaperAccountStatus
from bist_signal_bot.signals.models import SignalCandidate, SignalDirection
from bist_signal_bot.risk.models import RiskDecision, RiskDecisionStatus, RiskFilterResult

def test_order_reject_if_account_not_active():
    manager = PaperOrderManager()
    acc = PaperAccount(account_id="a", initial_cash=100, cash=100, equity=100, status=PaperAccountStatus.PAUSED)
    order = manager.create_market_order("a", "ASELS", PaperOrderSide.BUY, 10)
    manager.validate_order_against_account(order, acc)
    assert order.status == PaperOrderStatus.REJECTED

def test_order_creates_with_metadata():
    manager = PaperOrderManager()
    sig = SignalCandidate(symbol="ASELS", direction=SignalDirection.LONG, score=80.0, strategy_name="test")
    # Setting an arbitrary ID directly via metadata hack if it doesn't allow field setting easily,
    # or rely on its own generated ID. For now let's just make sure it creates order properly
    # sig.signal_id = "sig-123" # Not needed for order creation directly anymore
    order = manager.create_market_order("a", "ASELS", PaperOrderSide.BUY, 10, signal=sig)
    assert order.strategy_name == "test"

def test_order_risk_rejection():
    manager = PaperOrderManager()
    sig = SignalCandidate(symbol="ASELS", direction=SignalDirection.LONG, score=80.0, strategy_name="test")
    filter_res = RiskFilterResult(passed=False, status=RiskDecisionStatus.REJECTED, reasons=["too risky"])
    risk = RiskDecision(signal=sig, side=SignalDirection.LONG, approved=False, status=RiskDecisionStatus.REJECTED, filter_result=filter_res, issues=["too risky"])
    order = manager.create_market_order("a", "ASELS", PaperOrderSide.BUY, 10, risk_decision=risk)
    assert order.status == PaperOrderStatus.REJECTED

def test_order_accept_cancel():
    manager = PaperOrderManager()
    order = manager.create_market_order("a", "ASELS", PaperOrderSide.BUY, 10)
    manager.accept_order(order)
    assert order.status == PaperOrderStatus.ACCEPTED
    manager.cancel_order(order)
    assert order.status == PaperOrderStatus.CANCELLED
