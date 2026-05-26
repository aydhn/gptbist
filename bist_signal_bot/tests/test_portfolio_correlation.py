import pytest
import pandas as pd
from bist_signal_bot.portfolio_construction.correlation import CorrelationAnalyzer

def test_correlation_returns_matrix():
    analyzer = CorrelationAnalyzer()
    df = analyzer.returns_matrix(["ASELS", "THYAO"], lookback_days=10)
    assert not df.empty
    assert list(df.columns) == ["ASELS", "THYAO"]
    assert len(df) == 10

def test_correlation_high_pairs_and_clusters():
    analyzer = CorrelationAnalyzer()
    df = pd.DataFrame({
        "A": [1, 2, 3, 4, 5],
        "B": [1, 2, 3, 4, 5],
        "C": [5, 4, 3, 2, 1]
    })

    corr = analyzer.correlation_matrix(df)
    pairs = analyzer.pairwise_high_correlations(corr, 0.9)
    assert len(pairs) == 2 # A-B (1.0), and A-C / B-C are -1.0 so their abs is 1.0

    clusters = analyzer.build_clusters(corr, {"A": 0.5, "B": 0.5, "C": 0.0}, 0.9)
    assert len(clusters) > 0
    # A, B, C are all highly correlated (magnitude 1.0)
    assert len(clusters[0].symbols) == 3
