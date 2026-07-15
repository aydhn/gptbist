import pytest
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
