import pytest
import pandas as pd
from bist_signal_bot.data.comparison import MarketDataComparator

def test_data_comparator():
    comp = MarketDataComparator()
    left = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01', '2023-01-02']),
        'close': [10.0, 11.0],
        'volume': [100, 200]
    })
    right = pd.DataFrame({
        'date': pd.to_datetime(['2023-01-01', '2023-01-02']),
        'close': [10.0, 11.5], # Diff > 0.1% on second day
        'volume': [100, 215]   # Diff > 5% on second day
    })

    report = comp.compare("ASELS", "1d", left, right, "local", "yf", close_tolerance_pct=0.1, volume_tolerance_pct=5.0)

    assert report.status == "WARNING"
    assert report.price_diff_count == 1
    assert report.volume_diff_count == 1
    assert len(report.warnings) == 2
