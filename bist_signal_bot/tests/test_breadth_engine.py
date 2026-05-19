from datetime import datetime
import pandas as pd
from bist_signal_bot.breadth.engine import BreadthEngine
from bist_signal_bot.breadth.models import BreadthAnalysisRequest

class MockDataService:
    def get_historical_data(self, symbol, timeframe, source):
        return pd.DataFrame({"date": pd.date_range("2024-01-01", periods=10), "close": range(1, 11)})

def test_breadth_engine_analyze():
    engine = BreadthEngine(data_service=MockDataService())
    req = BreadthAnalysisRequest(
        symbols=["SYM1", "SYM2"],
        universe_name="TEST",
        source="local_file",
        timeframe="1d",
        save_snapshot=False
    )
    res = engine.analyze(req)
    assert res is not None
    assert res.snapshot.universe_name == "TEST"
    assert len(res.relative_strength_scores) == 2
