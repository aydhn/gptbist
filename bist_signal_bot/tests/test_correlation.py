import pandas as pd
import numpy as np

from bist_signal_bot.portfolio.correlation import CorrelationAnalyzer

def test_calculate_returns_matrix_happy_path():
    analyzer = CorrelationAnalyzer()

    df1 = pd.DataFrame({'close': [100, 101, 102, 103, 104]})
    df2 = pd.DataFrame({'close': [50, 52, 51, 53, 55]})
    data = {'SYM1': df1, 'SYM2': df2}

    res = analyzer.calculate_returns_matrix(data, lookback_rows=2)

    assert not res.empty
    assert list(res.columns) == ['SYM1', 'SYM2']
    assert len(res) == 2

    np.testing.assert_almost_equal(res.loc[3, 'SYM1'], 103/102 - 1)
    np.testing.assert_almost_equal(res.loc[4, 'SYM1'], 104/103 - 1)

    np.testing.assert_almost_equal(res.loc[3, 'SYM2'], 53/51 - 1)
    np.testing.assert_almost_equal(res.loc[4, 'SYM2'], 55/53 - 1)

def test_calculate_returns_matrix_empty_input():
    analyzer = CorrelationAnalyzer()
    res = analyzer.calculate_returns_matrix({})
    assert res.empty

def test_calculate_returns_matrix_missing_col_or_empty_df():
    analyzer = CorrelationAnalyzer()

    df1 = pd.DataFrame()
    df2 = pd.DataFrame({'open': [100, 101, 102]})

    data = {'SYM1': df1, 'SYM2': df2}
    res = analyzer.calculate_returns_matrix(data, lookback_rows=2)
    assert res.empty

def test_calculate_returns_matrix_mixed_valid_invalid():
    analyzer = CorrelationAnalyzer()

    df1 = pd.DataFrame({'close': [100, 101, 102]})
    df2 = pd.DataFrame({'open': [50, 52, 51]})

    data = {'SYM1': df1, 'SYM2': df2}
    res = analyzer.calculate_returns_matrix(data, lookback_rows=2)

    assert not res.empty
    assert list(res.columns) == ['SYM1']
    assert len(res) == 2
    np.testing.assert_almost_equal(res.loc[1, 'SYM1'], 101/100 - 1)
    np.testing.assert_almost_equal(res.loc[2, 'SYM1'], 102/101 - 1)

def test_calculate_returns_matrix_custom_price_col():
    analyzer = CorrelationAnalyzer()

    df1 = pd.DataFrame({'adj_close': [100, 110, 121]})
    data = {'SYM1': df1}

    res = analyzer.calculate_returns_matrix(data, price_col="adj_close", lookback_rows=2)

    assert not res.empty
    assert list(res.columns) == ['SYM1']
    assert len(res) == 2
    np.testing.assert_almost_equal(res.loc[1, 'SYM1'], 110/100 - 1)
    np.testing.assert_almost_equal(res.loc[2, 'SYM1'], 121/110 - 1)

from datetime import datetime, timezone
from bist_signal_bot.portfolio.models import CorrelationMatrixResult

def test_average_portfolio_correlation_happy_path():
    analyzer = CorrelationAnalyzer()

    matrix = pd.DataFrame(
        [
            [1.0, 0.5, 0.2],
            [0.5, 1.0, 0.8],
            [0.2, 0.8, 1.0]
        ],
        index=['A', 'B', 'C'],
        columns=['A', 'B', 'C']
    )

    corr = CorrelationMatrixResult(
        symbols=['A', 'B', 'C'],
        matrix=matrix,
        lookback_rows=60,
        method='pearson',
        generated_at=datetime.now(timezone.utc),
        issues=[],
        metadata={}
    )

    avg_corr = analyzer.average_portfolio_correlation(['A', 'B', 'C'], corr)
    assert avg_corr is not None
    np.testing.assert_almost_equal(avg_corr, 0.5)

def test_average_portfolio_correlation_subset():
    analyzer = CorrelationAnalyzer()

    matrix = pd.DataFrame(
        [
            [1.0, 0.5, 0.2, 0.1],
            [0.5, 1.0, 0.8, 0.3],
            [0.2, 0.8, 1.0, 0.6],
            [0.1, 0.3, 0.6, 1.0]
        ],
        index=['A', 'B', 'C', 'D'],
        columns=['A', 'B', 'C', 'D']
    )

    corr = CorrelationMatrixResult(
        symbols=['A', 'B', 'C', 'D'],
        matrix=matrix,
        lookback_rows=60,
        method='pearson',
        generated_at=datetime.now(timezone.utc),
        issues=[],
        metadata={}
    )

    avg_corr = analyzer.average_portfolio_correlation(['A', 'B', 'D', 'INVALID'], corr)
    assert avg_corr is not None
    np.testing.assert_almost_equal(avg_corr, 0.3)

def test_average_portfolio_correlation_empty_matrix():
    analyzer = CorrelationAnalyzer()

    corr = CorrelationMatrixResult(
        symbols=[],
        matrix=pd.DataFrame(),
        lookback_rows=60,
        method='pearson',
        generated_at=datetime.now(timezone.utc),
        issues=[],
        metadata={}
    )

    avg_corr = analyzer.average_portfolio_correlation(['A', 'B'], corr)
    assert avg_corr is None

def test_average_portfolio_correlation_insufficient_symbols():
    analyzer = CorrelationAnalyzer()

    matrix = pd.DataFrame(
        [[1.0, 0.5], [0.5, 1.0]],
        index=['A', 'B'],
        columns=['A', 'B']
    )

    corr = CorrelationMatrixResult(
        symbols=['A', 'B'],
        matrix=matrix,
        lookback_rows=60,
        method='pearson',
        generated_at=datetime.now(timezone.utc),
        issues=[],
        metadata={}
    )

    avg_corr = analyzer.average_portfolio_correlation(['A', 'INVALID'], corr)
    assert avg_corr is None

    avg_corr2 = analyzer.average_portfolio_correlation(['X', 'Y'], corr)
    assert avg_corr2 is None

def test_average_portfolio_correlation_no_valid_values():
    analyzer = CorrelationAnalyzer()

    matrix = pd.DataFrame(
        [[1.0, np.nan], [np.nan, 1.0]],
        index=['A', 'B'],
        columns=['A', 'B']
    )

    corr = CorrelationMatrixResult(
        symbols=['A', 'B'],
        matrix=matrix,
        lookback_rows=60,
        method='pearson',
        generated_at=datetime.now(timezone.utc),
        issues=[],
        metadata={}
    )

    avg_corr = analyzer.average_portfolio_correlation(['A', 'B'], corr)
    assert avg_corr is None

def test_calculate_correlation_matrix_happy_path():
    analyzer = CorrelationAnalyzer()
    df1 = pd.DataFrame({'close': [100, 101, 102, 103, 104]})
    df2 = pd.DataFrame({'close': [50, 52, 51, 53, 55]})
    data = {'SYM1': df1, 'SYM2': df2}

    res = analyzer.calculate_correlation_matrix(data, lookback_rows=2)

    assert res.symbols == ['SYM1', 'SYM2']
    assert res.lookback_rows == 2
    assert res.method == "pearson"
    assert not res.matrix.empty
    assert res.matrix.shape == (2, 2)
    assert not res.issues

def test_calculate_correlation_matrix_empty_input():
    analyzer = CorrelationAnalyzer()
    res = analyzer.calculate_correlation_matrix({})

    assert res.symbols == []
    assert res.matrix.empty
    assert "No price data provided" in res.issues

def test_calculate_correlation_matrix_empty_returns():
    analyzer = CorrelationAnalyzer()
    # Providing empty dataframes will result in an empty returns matrix
    df1 = pd.DataFrame()
    data = {'SYM1': df1}

    res = analyzer.calculate_correlation_matrix(data)

    assert res.symbols == ['SYM1']
    assert res.matrix.empty
    assert "Could not compute valid returns matrix" in res.issues

def test_calculate_correlation_matrix_missing_symbols():
    analyzer = CorrelationAnalyzer()
    df1 = pd.DataFrame({'close': [100, 101, 102, 103, 104]})
    df2 = pd.DataFrame({'open': [50, 52, 51, 53, 55]}) # Missing 'close' col
    data = {'SYM1': df1, 'SYM2': df2}

    res = analyzer.calculate_correlation_matrix(data, lookback_rows=2)

    assert res.symbols == ['SYM1']
    assert not res.matrix.empty
    assert res.matrix.shape == (1, 1)

    missing_issue_found = any("Missing valid returns for symbols" in issue for issue in res.issues)
    assert missing_issue_found
    assert res.metadata.get("missing_symbols") == ['SYM2']
