import pandas as pd
import numpy as np

def safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator == 0 or pd.isna(denominator) or np.isinf(denominator):
        return None
    res = numerator / denominator
    if pd.isna(res) or np.isinf(res):
         return None
    return float(res)

def calculate_returns(equity_curve: pd.DataFrame, equity_col: str = "equity") -> pd.Series:
    if equity_curve.empty or equity_col not in equity_curve.columns:
        return pd.Series(dtype=float)
    return equity_curve[equity_col].pct_change().dropna()

def calculate_total_return(initial_capital: float, final_equity: float) -> float:
    if initial_capital <= 0:
        return 0.0
    return (final_equity - initial_capital) / initial_capital

def calculate_annualized_return(total_return: float, periods: int, periods_per_year: int = 252) -> float | None:
    if periods <= 0:
        return None
    years = periods / periods_per_year
    if years <= 0:
         return None
    return (1.0 + total_return) ** (1.0 / years) - 1.0

def calculate_annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float | None:
    if len(returns) < 2:
        return None
    vol = returns.std()
    if pd.isna(vol) or np.isinf(vol):
        return None
    return float(vol * np.sqrt(periods_per_year))

def calculate_downside_volatility(returns: pd.Series, periods_per_year: int = 252) -> float | None:
    if len(returns) < 2:
        return None
    downside_returns = returns[returns < 0]
    if len(downside_returns) < 2:
        return 0.0
    downside_vol = np.sqrt(np.mean(downside_returns**2))
    return float(downside_vol * np.sqrt(periods_per_year))

def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float | None:
    vol = calculate_annualized_volatility(returns, periods_per_year)
    if not vol or vol == 0:
        return None
    ann_return = calculate_annualized_return(
        total_return=(1+returns).prod() - 1,
        periods=len(returns),
        periods_per_year=periods_per_year
    )
    if ann_return is None:
         return None
    return safe_divide(ann_return - risk_free_rate, vol)

def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float | None:
    downside_vol = calculate_downside_volatility(returns, periods_per_year)
    if downside_vol is None or downside_vol == 0:
        return None
    ann_return = calculate_annualized_return(
        total_return=(1+returns).prod() - 1,
        periods=len(returns),
        periods_per_year=periods_per_year
    )
    if ann_return is None:
         return None
    return safe_divide(ann_return - risk_free_rate, downside_vol)

def calculate_calmar_ratio(annualized_return: float | None, max_drawdown_pct: float | None) -> float | None:
    if annualized_return is None or max_drawdown_pct is None or max_drawdown_pct == 0:
        return None
    return safe_divide(annualized_return, abs(max_drawdown_pct / 100.0))

def calculate_var_cvar(returns: pd.Series, confidence: float = 0.95) -> tuple[float | None, float | None]:
    if len(returns) < 5:
        return None, None
    var = np.percentile(returns, (1 - confidence) * 100)
    cvar_returns = returns[returns <= var]
    cvar = cvar_returns.mean() if len(cvar_returns) > 0 else var
    return float(var), float(cvar)
