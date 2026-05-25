from bist_signal_bot.monte_carlo.distributions import DistributionAnalyzer
from bist_signal_bot.monte_carlo.models import MonteCarloMetricType

def test_distribution_percentiles():
    analyzer = DistributionAnalyzer()
    values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    dist = analyzer.build_distribution(MonteCarloMetricType.TOTAL_RETURN, values)
    assert dist.percentiles["p50"] == 5.5
    assert abs(dist.percentiles["p95"] - 9.55) < 1e-5

def test_percentile_rank():
    analyzer = DistributionAnalyzer()
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    rank = analyzer.percentile_rank(values, 3.0)
    assert abs(rank - 50.0) < 1e-5

def test_summary_metric():
    analyzer = DistributionAnalyzer()
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    dist = analyzer.build_distribution(MonteCarloMetricType.TOTAL_RETURN, values)
    metric = analyzer.summary_metric(dist)

    assert metric.mean == 3.0
    assert metric.median == 3.0
    assert metric.min_value == 1.0
    assert metric.max_value == 5.0
