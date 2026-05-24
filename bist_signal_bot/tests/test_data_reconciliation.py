import pytest
import pandas as pd
from datetime import datetime
from bist_signal_bot.data.data_quality import DataReconciliationEngine

def test_reconciliation_close_mismatch():
    df_a = pd.DataFrame({"Close": [10.0, 11.0]}, index=[datetime(2021,1,1), datetime(2021,1,2)])
    df_b = pd.DataFrame({"Close": [10.0, 11.5]}, index=[datetime(2021,1,1), datetime(2021,1,2)])

    engine = DataReconciliationEngine()
    res = engine.compare_providers("A", df_a, df_b, "pa", "pb")
    assert res.mismatches == 1

def test_duplicate_bars():
    df = pd.DataFrame({"Close": [10.0, 11.0]}, index=[datetime(2021,1,1), datetime(2021,1,1)])
    engine = DataReconciliationEngine()
    issues = engine.detect_duplicate_bars(df)
    assert len(issues) == 1

def test_zero_price():
    df = pd.DataFrame({"Close": [10.0, 0.0]}, index=[datetime(2021,1,1), datetime(2021,1,2)])
    engine = DataReconciliationEngine()
    issues = engine.detect_invalid_prices(df)
    assert len(issues) == 1
