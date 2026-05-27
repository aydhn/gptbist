from datetime import datetime
from bist_signal_bot.valuation.bands import ValuationBandAnalyzer
from bist_signal_bot.valuation.models import ValuationMultiple, ValuationMetricType, ValuationStatus

def test_band_analyzer_percentile_and_zscore():
    analyzer = ValuationBandAnalyzer()
    values = [10.0, 12.0, 14.0, 16.0, 18.0]

    assert analyzer.percentile_rank(values, 14.0) == 50.0
    assert analyzer.percentile_rank(values, 10.0) == 10.0 # 0 below + 0.5 equal / 5
    assert round(analyzer.z_score(values, 14.0), 2) == 0.0

def test_band_insufficient_history():
    analyzer = ValuationBandAnalyzer()
    analyzer.min_history = 10

    mult = ValuationMultiple(multiple_id="1", symbol="TEST", metric_type=ValuationMetricType.PE, as_of=datetime.utcnow(), value=10.0, status=ValuationStatus.FAIR)

    band = analyzer.build_historical_band("TEST", ValuationMetricType.PE, [mult])
    assert band.status == ValuationStatus.INSUFFICIENT_DATA
