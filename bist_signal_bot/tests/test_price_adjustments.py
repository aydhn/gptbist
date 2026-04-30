from datetime import date, datetime, UTC
import pandas as pd
import pytest

from bist_signal_bot.data.models import (
    MarketDataFrame, Timeframe, DataVendor, CorporateAction, CorporateActionType, AdjustmentPolicy, AdjustmentStatus
)
from bist_signal_bot.data.adjustments import PriceAdjustmentEngine

from bist_signal_bot.data.corporate_actions import CorporateActionStore

@pytest.fixture
def mock_market_data():
    dates = pd.date_range(start="2025-06-25", end="2025-07-05", freq="B")
    df = pd.DataFrame({
        "open": [10.0] * len(dates),
        "high": [11.0] * len(dates),
        "low": [9.0] * len(dates),
        "close": [10.0] * len(dates),
        "volume": [1000.0] * len(dates)
    }, index=dates)
    df.index.name = "timestamp"

    return MarketDataFrame(
        symbol="ASELS",
        timeframe=Timeframe.DAILY,
        source=DataVendor.MOCK,
        data=df,
        fetched_at=datetime.now(UTC),
        adjusted=False
    )

def test_flag_only_policy(mock_market_data):
    engine = PriceAdjustmentEngine(policy=AdjustmentPolicy.FLAG_ONLY)

    # We will simulate extreme return manually on the mock dataframe
    mock_market_data.data.loc["2025-07-02", "close"] = 15.0 # 50% jump

    result = engine.adjust_market_data(mock_market_data)

    assert result.report.status == AdjustmentStatus.SUCCESS
    assert result.report.policy == AdjustmentPolicy.FLAG_ONLY
    assert result.report.actions_applied == 0
    assert result.market_data.data.loc["2025-07-02", "close"] == 15.0 # Unmodified

    # Verify extreme return was flagged
    assert any(i.issue_type == "POTENTIAL_UNADJUSTED_EVENT" for i in result.report.issues)

def test_manual_split_adjust(mock_market_data):
    # Setup action store mock via passing actions directly to the engine function
    engine = PriceAdjustmentEngine(policy=AdjustmentPolicy.MANUAL_SPLIT_ADJUST)

    actions = [
        CorporateAction(symbol="ASELS", action_date=date(2025, 7, 1), action_type=CorporateActionType.SPLIT, ratio=2.0)
    ]

    # Let's override adjust_market_data's action loading just for this test
    # Actually, apply_split_adjustments takes actions directly
    df_adj, issues = engine.apply_split_adjustments(mock_market_data.data, actions)

    assert len(issues) == 1
    assert issues[0].issue_type == "APPLIED_SPLIT"

    # Dates before 2025-07-01 should be adjusted (price / 2, vol * 2)
    assert df_adj.loc["2025-06-30", "close"] == 5.0
    assert df_adj.loc["2025-06-30", "volume"] == 2000.0

    # Dates on or after 2025-07-01 should be unadjusted
    assert df_adj.loc["2025-07-01", "close"] == 10.0
    assert df_adj.loc["2025-07-01", "volume"] == 1000.0

def test_manual_reverse_split_adjust(mock_market_data):
    engine = PriceAdjustmentEngine(policy=AdjustmentPolicy.MANUAL_SPLIT_ADJUST)

    # Reverse split 10:1
    actions = [
        CorporateAction(symbol="ASELS", action_date=date(2025, 7, 1), action_type=CorporateActionType.REVERSE_SPLIT, ratio=10.0)
    ]

    df_adj, issues = engine.apply_split_adjustments(mock_market_data.data, actions)

    # Dates before 2025-07-01 should be adjusted (price * 10, vol / 10)
    assert df_adj.loc["2025-06-30", "close"] == 100.0
    assert df_adj.loc["2025-06-30", "volume"] == 100.0

    # Dates on or after 2025-07-01 should be unadjusted
    assert df_adj.loc["2025-07-01", "close"] == 10.0

def test_use_provider_adjusted(mock_market_data):
    engine = PriceAdjustmentEngine(policy=AdjustmentPolicy.USE_PROVIDER_ADJUSTED, strict=False)

    # Missing adj_close
    df_adj, issues = engine.apply_provider_adjusted(mock_market_data.data)
    assert len(issues) == 1
    assert issues[0].issue_type == "MISSING_ADJ_CLOSE"

    # Add adj_close
    mock_market_data.data["adj_close"] = mock_market_data.data["close"].copy()
    # Mock an adjustment (2:1 split effect across whole series)
    mock_market_data.data.loc[:"2025-06-30", "adj_close"] = 5.0

    df_adj, issues = engine.apply_provider_adjusted(mock_market_data.data)

    assert len(issues) == 1
    assert issues[0].issue_type == "APPLIED_PROVIDER_ADJUSTED"

    # Check factor application (adj_close/close = 5/10 = 0.5)
    # open * 0.5
    assert df_adj.loc["2025-06-30", "open"] == 5.0
    # volume / 0.5
    assert df_adj.loc["2025-06-30", "volume"] == 2000.0

    # Check unaffected rows
    assert df_adj.loc["2025-07-01", "open"] == 10.0
    assert df_adj.loc["2025-07-01", "volume"] == 1000.0

def test_adjust_market_data_engine_flow(tmp_path, mock_market_data):
    from bist_signal_bot.config.settings import Settings

    # Mock settings and store
    settings = Settings(CORPORATE_ACTIONS_DIR_NAME="store", CORPORATE_ACTIONS_FILE_NAME="actions.json")
    store = CorporateActionStore(settings, base_dir=tmp_path)
    store.initialize_empty()
    store.add_action(CorporateAction(symbol="ASELS", action_date=date(2025, 7, 1), action_type=CorporateActionType.SPLIT, ratio=2.0))

    engine = PriceAdjustmentEngine(settings=settings, action_store=store, policy=AdjustmentPolicy.MANUAL_SPLIT_ADJUST)
    result = engine.adjust_market_data(mock_market_data)

    assert result.report.status == AdjustmentStatus.SUCCESS
    assert result.report.actions_applied == 1
    assert result.market_data.metadata["adjusted_by_engine"] is True
    assert result.market_data.adjusted is True
    assert result.market_data.data.loc["2025-06-30", "close"] == 5.0
