import pytest
import pandas as pd
import numpy as np

from bist_signal_bot.portfolio.correlation import CorrelationAnalyzer
from datetime import datetime, timezone
from bist_signal_bot.portfolio.models import CorrelationMatrixResult

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

def test_correlation_warnings_empty_matrix():
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
    warnings = analyzer.correlation_warnings(["AAPL"], ["MSFT"], corr, 0.8)
    assert warnings == ["Correlation matrix is empty, correlation checks bypassed"]

def test_correlation_warnings_missing_candidate():
    analyzer = CorrelationAnalyzer()
    matrix = pd.DataFrame(
        [[1.0]], index=['MSFT'], columns=['MSFT']
    )
    corr = CorrelationMatrixResult(
        symbols=['MSFT'],
        matrix=matrix,
        lookback_rows=60,
        method='pearson',
        generated_at=datetime.now(timezone.utc),
        issues=[],
        metadata={}
    )
    warnings = analyzer.correlation_warnings(["AAPL"], ["MSFT"], corr, 0.8)
    assert warnings == ["No correlation data for candidate AAPL"]

def test_correlation_warnings_high_correlation():
    analyzer = CorrelationAnalyzer()
    matrix = pd.DataFrame(
        [[1.0, 0.9], [0.9, 1.0]], index=['AAPL', 'MSFT'], columns=['AAPL', 'MSFT']
    )
    corr = CorrelationMatrixResult(
        symbols=['AAPL', 'MSFT'],
        matrix=matrix,
        lookback_rows=60,
        method='pearson',
        generated_at=datetime.now(timezone.utc),
        issues=[],
        metadata={}
    )
    warnings = analyzer.correlation_warnings(["AAPL"], ["MSFT"], corr, 0.8)
    assert len(warnings) == 1
    assert "Candidate AAPL has high correlation (0.90) with existing portfolio > 0.8" in warnings[0]

def test_correlation_warnings_low_correlation():
    analyzer = CorrelationAnalyzer()
    matrix = pd.DataFrame(
        [[1.0, 0.5], [0.5, 1.0]], index=['AAPL', 'MSFT'], columns=['AAPL', 'MSFT']
    )
    corr = CorrelationMatrixResult(
        symbols=['AAPL', 'MSFT'],
        matrix=matrix,
        lookback_rows=60,
        method='pearson',
        generated_at=datetime.now(timezone.utc),
        issues=[],
        metadata={}
    )
    warnings = analyzer.correlation_warnings(["AAPL"], ["MSFT"], corr, 0.8)
    assert warnings == []

def test_correlation_warnings_max_c_none():
    analyzer = CorrelationAnalyzer()
    matrix = pd.DataFrame(
        [[1.0]], index=['AAPL'], columns=['AAPL']
    )
    corr = CorrelationMatrixResult(
        symbols=['AAPL'],
        matrix=matrix,
        lookback_rows=60,
        method='pearson',
        generated_at=datetime.now(timezone.utc),
        issues=[],
        metadata={}
    )
    warnings = analyzer.correlation_warnings(["AAPL"], ["MSFT"], corr, 0.8)
    assert warnings == []
