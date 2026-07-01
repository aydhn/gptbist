import pytest
import pandas as pd
from datetime import datetime, UTC
from bist_signal_bot.paper.execution import PaperExecutionSimulator
from bist_signal_bot.paper.orders import PaperOrderManager
from bist_signal_bot.paper.models import PaperOrderSide, PaperExecutionMode, PaperLedgerState, PaperAccount, CreateMarketOrderRequest
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import PaperExecutionError

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "open": [10.0, 11.0],
        "high": [12.0, 13.0],
        "low": [9.0, 10.0],
        "close": [11.0, 12.0]
    })

def test_execution_latest_close(sample_df):
    # 17. LATEST_CLOSE_RESEARCH son close fiyatını kullanır.
    sim = PaperExecutionSimulator(settings=Settings())
    om = PaperOrderManager()
    order = om.create_market_order(CreateMarketOrderRequest(account_id="a", symbol="ASELS", side=PaperOrderSide.BUY, quantity=10))
    om.accept_order(order)

    fill = sim.simulate_fill(order, data=sample_df, mode=PaperExecutionMode.LATEST_CLOSE_RESEARCH)
    assert fill.fill_price == 12.0

def test_execution_manual_price(sample_df):
    # 18. MANUAL_PRICE manual price kullanır.
    # 19. manual price yoksa hata üretir.
    sim = PaperExecutionSimulator(settings=Settings())
    om = PaperOrderManager()
    order = om.create_market_order(CreateMarketOrderRequest(account_id="a", symbol="ASELS", side=PaperOrderSide.BUY, quantity=10))
    om.accept_order(order)

    fill = sim.simulate_fill(order, mode=PaperExecutionMode.MANUAL_PRICE, manual_price=15.0)
    assert fill.fill_price == 15.0

    with pytest.raises(PaperExecutionError):
        sim.simulate_fill(order, mode=PaperExecutionMode.MANUAL_PRICE)

def test_execution_buy_logic(sample_df):
    # 20. BUY fill cash düşürür.
    # 21. BUY fill pozisyon açar.
    # 22. İkinci BUY avg_entry_price günceller.
    sim = PaperExecutionSimulator(settings=Settings())
    om = PaperOrderManager()

    acc = PaperAccount(account_id="a", initial_cash=1000, cash=1000, equity=1000)
    state = PaperLedgerState(account=acc)

    order1 = om.create_market_order(CreateMarketOrderRequest(account_id="a", symbol="ASELS", side=PaperOrderSide.BUY, quantity=10))
    om.accept_order(order1)
    fill1 = sim.simulate_fill(order1, mode=PaperExecutionMode.MANUAL_PRICE, manual_price=10.0)
    # Assume 0 cost for simple test if cost engine not fully configured, but default cost engine might add small BPS
    state = sim.apply_fill_to_ledger(state, fill1)

    assert state.account.cash < 1000
    assert len(state.open_positions()) == 1
    assert state.open_positions()[0].quantity == 10

    order2 = om.create_market_order(CreateMarketOrderRequest(account_id="a", symbol="ASELS", side=PaperOrderSide.BUY, quantity=10))
    om.accept_order(order2)
    fill2 = sim.simulate_fill(order2, mode=PaperExecutionMode.MANUAL_PRICE, manual_price=20.0)
    state = sim.apply_fill_to_ledger(state, fill2)

    assert state.open_positions()[0].quantity == 20
    # Avg price should be ~15
    assert 14 < state.open_positions()[0].avg_entry_price < 16

def test_execution_sell_logic():
    # 23. SELL fill pozisyonu azaltır.
    # 24. SELL fill pozisyonu kapatır ve realized pnl hesaplar.
    sim = PaperExecutionSimulator(settings=Settings())
    om = PaperOrderManager()

    acc = PaperAccount(account_id="a", initial_cash=1000, cash=1000, equity=1000)
    state = PaperLedgerState(account=acc)

    o_buy = om.create_market_order(CreateMarketOrderRequest(account_id="a", symbol="A", side=PaperOrderSide.BUY, quantity=10))
    om.accept_order(o_buy)
    f_buy = sim.simulate_fill(o_buy, mode=PaperExecutionMode.MANUAL_PRICE, manual_price=10.0)
    state = sim.apply_fill_to_ledger(state, f_buy)

    o_sell1 = om.create_market_order(CreateMarketOrderRequest(account_id="a", symbol="A", side=PaperOrderSide.SELL, quantity=5))
    om.accept_order(o_sell1)
    f_sell1 = sim.simulate_fill(o_sell1, mode=PaperExecutionMode.MANUAL_PRICE, manual_price=15.0)
    state = sim.apply_fill_to_ledger(state, f_sell1)

    assert state.open_positions()[0].quantity == 5
    assert state.account.realized_pnl > 0

    o_sell2 = om.create_market_order(CreateMarketOrderRequest(account_id="a", symbol="A", side=PaperOrderSide.SELL, quantity=5))
    om.accept_order(o_sell2)
    f_sell2 = sim.simulate_fill(o_sell2, mode=PaperExecutionMode.MANUAL_PRICE, manual_price=15.0)
    state = sim.apply_fill_to_ledger(state, f_sell2)

    assert len(state.open_positions()) == 0

def test_execution_rejections():
    # 25. Yetersiz cash BUY işlemi reject eder.
    # 26. Açık pozisyon yokken SELL reject eder.
    settings = Settings()
    settings.PAPER_REJECT_IF_INSUFFICIENT_CASH = True
    sim = PaperExecutionSimulator(settings=settings)
    om = PaperOrderManager()

    acc = PaperAccount(account_id="a", initial_cash=100, cash=100, equity=100)
    state = PaperLedgerState(account=acc)

    o_buy = om.create_market_order(CreateMarketOrderRequest(account_id="a", symbol="A", side=PaperOrderSide.BUY, quantity=100))
    om.accept_order(o_buy)
    f_buy = sim.simulate_fill(o_buy, mode=PaperExecutionMode.MANUAL_PRICE, manual_price=10.0) # Cost 1000 > cash

    with pytest.raises(PaperExecutionError):
         sim.apply_fill_to_ledger(state, f_buy)

    o_sell = om.create_market_order(CreateMarketOrderRequest(account_id="a", symbol="B", side=PaperOrderSide.SELL, quantity=10))
    om.accept_order(o_sell)
    f_sell = sim.simulate_fill(o_sell, mode=PaperExecutionMode.MANUAL_PRICE, manual_price=10.0)

    with pytest.raises(PaperExecutionError):
         sim.apply_fill_to_ledger(state, f_sell)

def test_mark_to_market():
    # 28. mark_to_market equity günceller.
    sim = PaperExecutionSimulator(settings=Settings())
    om = PaperOrderManager()

    acc = PaperAccount(account_id="a", initial_cash=1000, cash=1000, equity=1000)
    state = PaperLedgerState(account=acc)

    o_buy = om.create_market_order(CreateMarketOrderRequest(account_id="a", symbol="A", side=PaperOrderSide.BUY, quantity=10))
    om.accept_order(o_buy)
    f_buy = sim.simulate_fill(o_buy, mode=PaperExecutionMode.MANUAL_PRICE, manual_price=10.0)
    state = sim.apply_fill_to_ledger(state, f_buy)

    state = sim.mark_to_market(state, {"A": 20.0})
    assert state.open_positions()[0].market_value == 200.0
    assert state.open_positions()[0].unrealized_pnl > 80.0 # roughly 100
