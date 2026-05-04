import pytest
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from bist_signal_bot.backtesting.reporting import BacktestReportWriter
from bist_signal_bot.backtesting.models import (
    BacktestResult, BacktestConfig, ExecutionPriceMode, CostScenario, BacktestMode
)

@pytest.fixture
def mock_result():
    config = BacktestConfig(
        initial_capital=10000.0,
        execution_price_mode=ExecutionPriceMode.NEXT_OPEN,
        commission_enabled=True,
        slippage_enabled=True,
        allow_short=False,
        max_position_size_pct=0.1,
        min_trade_notional=100.0,
        trade_on_candidate_statuses=["ACTIVE"],
        close_on_opposite_signal=True,
        close_on_flat_signal=False,
        one_position_per_symbol=True,
        use_fractional_shares=False,
        close_open_positions_at_end=True,
        scenario=CostScenario.BASE
    )

    eq_df = pd.DataFrame({
        "timestamp": pd.date_range("2023-01-01", periods=6),
        "cash": [10000]*6,
        "position_value": [0]*6,
        "equity": [10000, 10100, 10050, 9950, 10000, 9996],
        "gross_exposure": [0]*6,
        "net_exposure": [0]*6,
        "open_positions": [0]*6
    }).set_index("timestamp")

    return BacktestResult(
        strategy_name="test_strat",
        mode=BacktestMode.SINGLE_SYMBOL,
        config=config,
        trades=[],
        fills=[],
        portfolio_snapshots=[],
        orders=[],
        started_at=datetime(2023,1,1),
        finished_at=datetime(2023,1,7),
        elapsed_seconds=1.0,
        issues=[],
        symbol="ASELS",
        equity_curve=eq_df
    )

def test_build_report_bundle(mock_result):
    writer = BacktestReportWriter()
    bundle = writer.build_report_bundle(mock_result)

    assert bundle.performance_report.strategy_name == "test_strat"
    assert bundle.performance_report.symbol == "ASELS"
    assert not bundle.drawdown_curve.empty

def test_save_json(mock_result, tmp_path):
    writer = BacktestReportWriter(base_dir=tmp_path)
    bundle = writer.build_report_bundle(mock_result)

    path = writer.save_json(bundle)
    assert path.exists()

    with open(path, "r") as f:
        data = json.load(f)

    assert "performance_report" in data
    assert data["performance_report"]["strategy_name"] == "test_strat"

def test_save_markdown(mock_result, tmp_path):
    writer = BacktestReportWriter(base_dir=tmp_path)
    bundle = writer.build_report_bundle(mock_result)

    path = writer.save_markdown(bundle)
    assert path.exists()

    with open(path, "r") as f:
        content = f.read()

    assert "# Backtest Report: test_strat (ASELS)" in content
    assert "Disclaimer" in content

def test_save_csv_files(mock_result, tmp_path):
    writer = BacktestReportWriter(base_dir=tmp_path)
    bundle = writer.build_report_bundle(mock_result)

    paths = writer.save_csv_files(bundle)
    assert "equity_curve" in paths
    assert "drawdown_curve" in paths

    assert paths["equity_curve"].exists()
    assert paths["drawdown_curve"].exists()
