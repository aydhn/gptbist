from datetime import datetime
import pandas as pd
from bist_signal_bot.features.breadth_features import BreadthFeatureBuilder
from bist_signal_bot.breadth.models import BreadthSnapshot, BreadthStatus

class MockEngine:
    def build_feature_snapshot(self, symbol, as_of_date):
        return {
            "status_code": BreadthStatus.STRONG.value,
            "composite_score": 85.0
        }

def test_breadth_features():
    engine = MockEngine()
    builder = BreadthFeatureBuilder(engine)

    df = pd.DataFrame({"date": [datetime(2024,1,1)], "close": [100]})
    res = builder.add_breadth_feature_columns(df, "SYM1")

    assert "breadth_status_code" in res.columns
    assert "breadth_composite_score" in res.columns
    assert res.iloc[0]["breadth_composite_score"] == 85.0
