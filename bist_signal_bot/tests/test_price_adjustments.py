import pytest
from datetime import datetime
import pandas as pd
from bist_signal_bot.corporate_actions.models import CorporateActionRecord, CorporateActionType, CorporateActionStatus, AdjustmentDirection
from bist_signal_bot.corporate_actions.adjustments import PriceAdjustmentEngine

def test_ca_validation_negative():
    with pytest.raises(ValueError):
        CorporateActionRecord(
            action_id="1", symbol="A", action_type=CorporateActionType.CASH_DIVIDEND,
            status=CorporateActionStatus.CONFIRMED, effective_date=datetime(2021,1,1),
            cash_amount=-1.0, source="test"
        )

def test_price_adjustment_engine_split():
    engine = PriceAdjustmentEngine()
    ca = CorporateActionRecord(
        action_id="1", symbol="A", action_type=CorporateActionType.STOCK_SPLIT,
        status=CorporateActionStatus.CONFIRMED, effective_date=datetime(2021,1,1),
        ratio=1.0, source="test" # 100% bonus/split -> ratio=1 -> factor=0.5
    )
    factor = engine.calculate_factor(ca)
    assert factor == 0.5

def test_price_adjustment_engine_no_mutate():
    df = pd.DataFrame({"Open": [10.0], "High": [12.0], "Low": [9.0], "Close": [11.0], "Volume": [100.0]}, index=[datetime(2020,12,31)])
    engine = PriceAdjustmentEngine()
    ca = CorporateActionRecord(
        action_id="1", symbol="A", action_type=CorporateActionType.STOCK_SPLIT,
        status=CorporateActionStatus.CONFIRMED, effective_date=datetime(2021,1,1),
        ratio=1.0, source="test"
    )
    df_copy = df.copy()
    adj_df = engine.apply_adjustments("A", df, [ca], AdjustmentDirection.BACKWARD)

    assert 'adj_close' in adj_df.columns
    assert adj_df.iloc[0]['adj_close'] == 5.5
    assert df.equals(df_copy) # Input unmutated
