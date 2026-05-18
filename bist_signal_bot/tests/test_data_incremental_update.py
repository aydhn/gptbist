import pytest
import pandas as pd
from datetime import datetime, timedelta
from bist_signal_bot.data.incremental import IncrementalUpdatePlanner

def test_incremental_planner_no_data():
    planner = IncrementalUpdatePlanner()
    plan = planner.plan_update("ASELS", "1d", None)
    assert plan["action"] == "FULL_FETCH"
    assert plan["start_date"] is None

def test_incremental_planner_with_data():
    planner = IncrementalUpdatePlanner()
    end_dt = datetime.utcnow()
    df = pd.DataFrame({'date': [end_dt - timedelta(days=10)]})
    plan = planner.plan_update("ASELS", "1d", df, target_end=end_dt)
    assert plan["action"] == "INCREMENTAL_FETCH"
    assert plan["start_date"] is not None

def test_merge_incremental():
    planner = IncrementalUpdatePlanner()
    existing = pd.DataFrame({'date': pd.to_datetime(['2023-01-01']), 'close': [10]})
    new_data = pd.DataFrame({'date': pd.to_datetime(['2023-01-01', '2023-01-02']), 'close': [11, 12]})

    merged = planner.merge_incremental_data(existing, new_data)
    assert len(merged) == 2
    # Ensure new data overwrites existing on same date
    assert merged.loc[merged['date'] == '2023-01-01', 'close'].iloc[0] == 11
