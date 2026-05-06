import pandas as pd
from bist_signal_bot.portfolio.correlation import CorrelationAnalyzer

def test_correlation_returns_matrix():
    analyzer = CorrelationAnalyzer()
    df1 = pd.DataFrame({"close": [10, 11, 12, 11, 10]})
    df2 = pd.DataFrame({"close": [10, 11, 12, 11, 10]})

    res = analyzer.calculate_returns_matrix({"A": df1, "B": df2}, lookback_rows=5)
    assert len(res) == 4

def test_correlation_matrix_pearson():
    analyzer = CorrelationAnalyzer()
    df1 = pd.DataFrame({"close": [10, 11, 12, 11, 10]})
    df2 = pd.DataFrame({"close": [10, 11, 12, 11, 10]})

    res = analyzer.calculate_correlation_matrix({"A": df1, "B": df2})
    assert "A" in res.symbols
    assert res.matrix.loc["A", "B"] > 0.99

def test_max_pairwise_correlation():
    analyzer = CorrelationAnalyzer()
    df1 = pd.DataFrame({"close": [10, 11, 12, 11, 10]})
    df2 = pd.DataFrame({"close": [10, 11, 12, 11, 10]})
    res = analyzer.calculate_correlation_matrix({"A": df1, "B": df2})

    max_c = analyzer.max_pairwise_correlation("A", ["B"], res)
    assert max_c > 0.99

def test_correlation_missing_data_warning():
    analyzer = CorrelationAnalyzer()
    res = analyzer.calculate_correlation_matrix({})
    assert len(res.issues) > 0
