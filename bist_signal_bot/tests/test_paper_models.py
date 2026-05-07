import pytest
from bist_signal_bot.paper.models import PaperAccount, PaperOrder, PaperOrderSide, PaperOrderType, PaperOrderStatus, PaperFill, PaperExecutionMode, PaperLedgerState

def test_paper_account_validation():
    # 1. PaperAccount validation çalışır.
    with pytest.raises(ValueError):
        PaperAccount(account_id="", initial_cash=100, cash=100, equity=100)
    with pytest.raises(ValueError):
        PaperAccount(account_id="test", initial_cash=-100, cash=100, equity=100)

    acc = PaperAccount(account_id="test", initial_cash=1000, cash=1000, equity=1000)
    assert acc.account_id == "test"

def test_paper_order_symbol_normalization():
    # 2. PaperOrder symbol normalize eder.
    order = PaperOrder(
        order_id="1", account_id="acc", symbol="asels", side=PaperOrderSide.BUY,
        order_type=PaperOrderType.MARKET, status=PaperOrderStatus.CREATED, quantity=10
    )
    assert order.symbol == "ASELS"

def test_paper_order_quantity_negative():
    # 3. PaperOrder quantity negatifse hata üretir.
    with pytest.raises(ValueError):
        PaperOrder(
            order_id="1", account_id="acc", symbol="ASELS", side=PaperOrderSide.BUY,
            order_type=PaperOrderType.MARKET, status=PaperOrderStatus.CREATED, quantity=-10
        )

def test_paper_fill_cost_validation():
    # 4. PaperFill cost alanları negatif olamaz.
    with pytest.raises(ValueError):
        PaperFill(
            fill_id="1", order_id="1", account_id="acc", symbol="ASELS", side=PaperOrderSide.BUY,
            quantity=10, fill_price=10.0, effective_price=10.0, gross_notional=100.0,
            commission=-5.0, execution_mode=PaperExecutionMode.LATEST_CLOSE_RESEARCH
        )

def test_paper_ledger_state_open_positions():
    # 5. PaperLedgerState open_positions doğru döner.
    from bist_signal_bot.paper.models import PaperPosition, PaperPositionSide
    p1 = PaperPosition(position_id="1", account_id="acc", symbol="A", side=PaperPositionSide.LONG, quantity=10, avg_entry_price=1, last_price=1, market_value=10, is_open=True)
    p2 = PaperPosition(position_id="2", account_id="acc", symbol="B", side=PaperPositionSide.LONG, quantity=10, avg_entry_price=1, last_price=1, market_value=10, is_open=False)

    acc = PaperAccount(account_id="test", initial_cash=1000, cash=1000, equity=1000)
    state = PaperLedgerState(account=acc, positions=[p1, p2])

    open_pos = state.open_positions()
    assert len(open_pos) == 1
    assert open_pos[0].symbol == "A"
