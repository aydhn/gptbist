import pytest
from datetime import datetime
from bist_signal_bot.optimization.objectives import ObjectiveScorer
from bist_signal_bot.optimization.models import ObjectiveMetric, OptimizationConstraints
from bist_signal_bot.backtesting.models import (
    BacktestPerformanceReport, ReturnMetrics, RiskMetrics,
    RiskAdjustedMetrics, TradeMetrics, CostMetrics, ExposureMetrics
)

def build_mock_report(ret=10.0, sharpe=1.5, dd=-10.0, pf=1.2, trades=10):
    return BacktestPerformanceReport(
        strategy_name="mock", symbol="MOCK", timeframe="1d",
        initial_capital=100000, final_equity=110000,
        return_metrics=ReturnMetrics(
            total_return_pct=ret, annualized_return_pct=ret, cumulative_return_pct=ret,
            average_daily_return_pct=0.1, best_day_return_pct=1.0, worst_day_return_pct=-1.0
        ),
        risk_metrics=RiskMetrics(
            volatility_annualized_pct=15.0, downside_volatility_pct=10.0,
            max_drawdown_pct=dd, max_drawdown_duration_bars=5,
            value_at_risk_95_pct=-2.0, conditional_value_at_risk_95_pct=-3.0
        ),
        risk_adjusted_metrics=RiskAdjustedMetrics(
            sharpe_ratio=sharpe, sortino_ratio=sharpe*1.2, calmar_ratio=sharpe*0.8, return_over_max_drawdown=abs(ret/dd) if dd!=0 else 0
        ),
        trade_metrics=TradeMetrics(
            trade_count=trades, closed_trade_count=trades, winning_trades=trades//2,
            losing_trades=trades//2, breakeven_trades=0, win_rate_pct=50.0, loss_rate_pct=50.0,
            average_trade_return_pct=1.0, average_winner_pct=3.0, average_loser_pct=-1.0,
            best_trade_pct=5.0, worst_trade_pct=-3.0, gross_profit=20000, gross_loss=10000,
            net_profit=10000, profit_factor=pf, expectancy=1.0, average_bars_held=5.0
        ),
        cost_metrics=CostMetrics(
            total_commission=0, total_slippage=0, total_spread=0, total_tax=0, total_other_fees=0,
            total_cost=0, total_cost_bps=0, cost_as_pct_of_initial_capital=0, cost_as_pct_of_gross_profit=0
        ),
        exposure_metrics=ExposureMetrics(
            average_exposure_pct=50.0, max_exposure_pct=100.0, time_in_market_pct=80.0,
            average_open_positions=1.0, max_open_positions=1
        ),
        started_at=datetime.utcnow(), finished_at=datetime.utcnow(), generated_at=datetime.utcnow(),
        warnings=[], disclaimer="", metadata={}
    )

def test_objective_scorer_total_return():
    scorer = ObjectiveScorer()
    report = build_mock_report(ret=15.5)
    score, _ = scorer.score(report, ObjectiveMetric.TOTAL_RETURN)
    assert score == 15.5

def test_objective_scorer_sharpe():
    scorer = ObjectiveScorer()
    report = build_mock_report(sharpe=2.1)
    score, _ = scorer.score(report, ObjectiveMetric.SHARPE)
    assert score == 2.1

def test_objective_scorer_composite():
    scorer = ObjectiveScorer()
    report = build_mock_report(ret=50.0, sharpe=2.0, dd=-20.0, pf=1.5, trades=10)
    score, _ = scorer.score(report, ObjectiveMetric.COMPOSITE)
    assert 0.0 <= score <= 100.0

def test_objective_scorer_constraints_min_trades():
    scorer = ObjectiveScorer()
    report = build_mock_report(trades=2)
    constraints = OptimizationConstraints(min_trades=5)
    score, violations = scorer.score(report, ObjectiveMetric.TOTAL_RETURN, constraints)
    assert score == 0.0
    assert len(violations) > 0
    assert "min_trades" in violations[0]

def test_objective_scorer_constraints_max_dd():
    scorer = ObjectiveScorer()
    report = build_mock_report(dd=-30.0)
    constraints = OptimizationConstraints(max_drawdown_pct=20.0)
    score, violations = scorer.score(report, ObjectiveMetric.TOTAL_RETURN, constraints)
    assert score == 0.0
    assert len(violations) > 0
    assert "max_drawdown_pct" in violations[0]

def test_objective_scorer_constraints_positive_return():
    scorer = ObjectiveScorer()
    report = build_mock_report(ret=-5.0)
    constraints = OptimizationConstraints(require_positive_return=True)
    score, violations = scorer.score(report, ObjectiveMetric.TOTAL_RETURN, constraints)
    assert score == 0.0
    assert len(violations) > 0
