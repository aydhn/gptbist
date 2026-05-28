import json
from datetime import date, datetime
from enum import Enum
from typing import Any

def _json_default(obj: Any) -> Any:
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    raise TypeError(f"Type {type(obj)} not serializable")

def to_json_output(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, default=_json_default)

def format_key_values(data: dict[str, Any]) -> str:
    lines = []
    for k, v in data.items():
        if isinstance(v, dict):
            lines.append(f"{k}:")
            for sub_k, sub_v in v.items():
                lines.append(f"  {sub_k}: {sub_v}")
        else:
            lines.append(f"{k}: {v}")
    return "\n".join(lines)

def print_output(data: Any, as_json: bool = False) -> None:
    if as_json:
        print(to_json_output(data))
    else:
        if isinstance(data, dict):
            print(format_key_values(data))
        else:
            print(str(data))

def safe_float(value: Any, digits: int = 4) -> Any:
    if isinstance(value, float):
        return round(value, digits)
    return value

def format_success(message: str) -> str:
    return f"[SUCCESS] {message}"

def format_warning(message: str) -> str:
    return f"[WARNING] {message}"

def format_error(message: str) -> str:
    return f"[ERROR] {message}"

def format_cleaning_report(report) -> str:
    lines = [
        f"Symbol: {report.symbol}",
        f"Status: {report.status.value}",
        f"Input rows: {report.input_rows}",
        f"Output rows: {report.output_rows}",
        f"Dropped: {report.dropped_rows}",
        f"Filled: {report.filled_values}",
        f"Issues: {report.issue_count()}",
        f"Usable for Backtest: {report.usable_for_backtest}",
        f"Usable for ML: {report.usable_for_ml}"
    ]
    return "\n".join(lines)


def format_corporate_action_validation(report) -> str:
    lines = [
        "Corporate Actions Validation Report",
        f"Total: {report.total_actions} | Valid: {report.valid_actions} | Invalid: {report.invalid_actions} | Duplicates: {report.duplicate_actions}",
        f"Passed: {'Yes' if report.passed else 'No'}"
    ]
    if report.issues:
        lines.append("Issues:")
        for i in report.issues:
            lines.append(f"  - [{i.severity}] {i.issue_type} ({i.symbol}): {i.message}")
    return "\n".join(lines)

def format_adjustment_report(report) -> str:
    lines = [
        f"Adjustment Report for {report.symbol}",
        f"Policy: {report.policy.value} | Status: {report.status.value}",
        f"Input rows: {report.input_rows} | Output rows: {report.output_rows}",
        f"Actions available: {report.actions_available} | Applied: {report.actions_applied}",
        f"Adjusted columns: {', '.join(report.adjusted_columns) if report.adjusted_columns else 'None'}",
        f"Volume adjusted: {'Yes' if report.volume_adjusted else 'No'}",
        f"Issues: {report.issue_count()}"
    ]
    return "\n".join(lines)


def format_pattern_batch_result(result) -> str:
    lines = [
        "Pattern Feature Summary",
        f"Requested: {result.requested_count}",
        f"Success: {result.success_count}",
        f"Failed: {result.failed_count}",
        f"Elapsed: {safe_float(result.elapsed_seconds, 2)}s"
    ]

    if not result.output_data.empty:
        lines.append("Pattern features on last row:")
        last_row = result.output_data.iloc[-1]

        # Format close price if available
        if 'close' in last_row:
            lines.append(f"  close: {safe_float(last_row['close'], 2)}")

        # Add summary for available pattern features
        features_to_show = [
            'price_breakout_up_20', 'price_breakout_down_20',
            'near_resistance_50', 'near_support_50',
            'candle_doji_0.1', 'breakout_pressure_score', 'sr_position_score'
        ]

        for feature in features_to_show:
            if feature in last_row:
                val = last_row[feature]
                # Format float nicely or show 1/0 for boolean flags
                if isinstance(val, (int, float)):
                    lines.append(f"  {feature}: {safe_float(val, 2)}")
                else:
                    lines.append(f"  {feature}: {val}")

    return "\n".join(lines)

try:
    import pandas as pd
except ImportError:
    pd = None


def format_multi_timeframe_result(result) -> str:
    lines = [
        "BIST Bot Multi-Timeframe Feature Özeti",
        "",
        f"Sembol: {result.symbol}",
        f"Base: {result.base_timeframe}",
        f"Higher: {', '.join(result.alignment_report.higher_timeframes)}",
        f"Output rows: {result.alignment_report.output_rows}",
        f"Eklenen kolon: {len(result.alignment_report.added_columns)}",
        f"Alignment: {result.alignment_report.alignment_mode.value}",
        ""
    ]

    if len(result.output_data) > 0:
        lines.append("Multi-timeframe feature summary on last row:")
        try:
            last_row = result.output_data.iloc[-1]
            if 'close' in last_row:
                lines.append(f"  close: {safe_float(last_row['close'], 2)}")

            for col in ['tf_1wk_sma_20', 'tf_1wk_rsi_14', 'tf_1mo_sma_10', 'w_sma_20', 'w_rsi_14', 'm_sma_10']:
                if col in last_row and not pd.isna(last_row[col]):
                    lines.append(f"  {col}: {safe_float(last_row[col], 2)}")
        except Exception:
            pass

    lines.append("")
    lines.append("Bu çıktı sinyal/tavsiye değildir.")
    return "\n".join(lines)

def format_benchmark_result(result) -> str:
    lines = [
        f"Benchmark: {result.request.benchmark_name}",
        f"Symbol: {result.request.symbol or 'N/A'}",
        f"Status: {result.status.value}",
        f"Elapsed: {safe_float(result.elapsed_seconds, 2)}s"
    ]

    if result.signals:
        signal = result.signals[0]
        lines.append(f"Intent: {signal.intent.value}")
        lines.append(f"Score: {safe_float(signal.score, 2)}")
        if signal.weight is not None:
             lines.append(f"Weight: {safe_float(signal.weight, 2)}")
        if signal.reference_price is not None:
            lines.append(f"Reference Price: {safe_float(signal.reference_price, 2)}")
        if signal.reasons:
            lines.append(f"Reason: {signal.reasons[0]}")
        lines.append(f"Disclaimer: {signal.disclaimer}")

    if result.issues:
        lines.append("Issues:")
        for issue in result.issues:
            lines.append(f"  - {issue}")

    return "\n".join(lines)


def format_benchmark_batch(batch) -> str:
    lines = [
        f"Benchmark Batch: {batch.benchmark_name}",
        f"Requested Symbols: {len(batch.requested_symbols)}",
        f"Success: {batch.success_count}",
        f"Failed: {batch.failed_count}",
        f"Elapsed: {safe_float(batch.elapsed_seconds, 2)}s",
        ""
    ]

    # Calculate totals
    longs = sum(1 for r in batch.results for s in r.signals if s.intent.value == "LONG")
    flats = sum(1 for r in batch.results for s in r.signals if s.intent.value == "FLAT")
    shorts = sum(1 for r in batch.results for s in r.signals if s.intent.value == "SHORT")

    lines.append(f"Long Intents: {longs}")
    lines.append(f"Flat Intents: {flats}")
    lines.append(f"Short Intents: {shorts}")

    return "\n".join(lines)

def format_backtest_summary(result) -> str:
    lines = [
        "==================================================",
        f" BACKTEST RESULTS: {result.strategy_name.upper()} ",
        "==================================================",
        f"Symbol          : {result.symbol or 'N/A'}",
        f"Mode            : {result.config.execution_price_mode.value}",
        f"Cost Scenario   : {result.config.scenario.value}",
        "--------------------------------------------------",
        f"Initial Capital : {result.config.initial_capital:,.2f}",
        f"Final Equity    : {result.final_equity():,.2f}",
        f"Total Return    : {result.total_return_pct():.2f}%",
        f"Total Costs     : {result.total_cost():,.2f}",
        "--------------------------------------------------",
        f"Trade Count     : {result.trade_count()}",
        f"Closed Trades   : {result.closed_trade_count()}",
        f"Elapsed Time    : {result.elapsed_seconds:.3f}s",
        "==================================================",
        result.disclaimer,
        "==================================================",
    ]
    return "\n".join(lines)

def format_backtest_report_text(bundle: 'BacktestReportBundle') -> str:
    from bist_signal_bot.backtesting.models import BacktestReportBundle

    pr = bundle.performance_report

    lines = [
        "========================================",
        "      BIST SIGNAL BOT BACKTEST REPORT   ",
        "========================================",
        f"Strategy: {pr.strategy_name}",
        f"Symbol: {pr.symbol or 'PORTFOLIO'}",
        f"Initial Capital: {pr.initial_capital:.2f}",
        f"Final Equity: {pr.final_equity:.2f}",
        f"Total Return: {pr.return_metrics.total_return_pct:.2f}%",
        f"Annualized Return: {pr.return_metrics.annualized_return_pct:.2f}%" if pr.return_metrics.annualized_return_pct else "Annualized Return: N/A",
        f"Max Drawdown: {pr.risk_metrics.max_drawdown_pct:.2f}%" if pr.risk_metrics.max_drawdown_pct is not None else "Max Drawdown: N/A",
        f"Sharpe Ratio: {pr.risk_adjusted_metrics.sharpe_ratio:.2f}" if pr.risk_adjusted_metrics.sharpe_ratio is not None else "Sharpe Ratio: N/A",
        f"Sortino Ratio: {pr.risk_adjusted_metrics.sortino_ratio:.2f}" if pr.risk_adjusted_metrics.sortino_ratio is not None else "Sortino Ratio: N/A",
        f"Win Rate: {pr.trade_metrics.win_rate_pct:.2f}%" if pr.trade_metrics.win_rate_pct is not None else "Win Rate: N/A",
        f"Profit Factor: {pr.trade_metrics.profit_factor:.2f}" if pr.trade_metrics.profit_factor is not None else "Profit Factor: N/A",
        f"Trade Count: {pr.trade_metrics.trade_count}",
        f"Total Cost: {pr.cost_metrics.total_cost:.2f}"
    ]

    if bundle.benchmark_comparisons:
        lines.append("----------------------------------------")
        lines.append("Benchmark Comparisons:")
        for comp in bundle.benchmark_comparisons:
            outperform = "Yes" if comp.outperform else "No"
            lines.append(f"  vs {comp.benchmark_name}: Excess Return = {comp.excess_return_pct:.2f}% | Outperform = {outperform}")

    lines.append("----------------------------------------")
    lines.append("Disclaimer:")
    lines.append(pr.disclaimer)
    lines.append("========================================")

    return "\n".join(lines)


def format_risk_decision_text(decision) -> str:
    from bist_signal_bot.risk.reporting import format_risk_decision_text as reporting_fmt
    return reporting_fmt(decision)

def format_risk_batch_text(batch) -> str:
    from bist_signal_bot.risk.reporting import format_risk_batch_text as reporting_fmt
    return reporting_fmt(batch)

def format_divergence_result(result, symbol: str | None = None) -> str:
    lines = [
        "Divergence Report",
        f"Symbol: {symbol or result.symbol}",
        f"Detected: {len(result.divergences)}",
        f"Elapsed: {safe_float(result.elapsed_seconds, 2)}s"
    ]
    return "\n".join(lines)

def format_optimization_text(result) -> str:
    from bist_signal_bot.optimization.reporting import format_optimization_text as fmt
    return fmt(result)


def print_ml_train_result(result):
    from bist_signal_bot.ml.training.reporting import format_ml_train_text
    print(format_ml_train_text(result))

def print_ml_prediction_result(result):
    from bist_signal_bot.ml.training.reporting import format_ml_prediction_text
    print(format_ml_prediction_text(result))

def format_job_text(job: Any) -> str:
    lines = [
        f"Job: {job.title} ({job.job_id})",
        f"Status: {job.status.value if hasattr(job.status, 'value') else str(job.status)}",
        f"Priority: {job.priority.value if hasattr(job.priority, 'value') else str(job.priority)}",
        f"Symbols: {','.join(job.symbols) if job.symbols else 'N/A'}"
    ]
    return "\n".join(lines)

def format_batch_plan_text(plan: Any) -> str:
    lines = [
        f"Research Batch Plan: {plan.plan_id}",
        f"Trigger: {plan.trigger.value if hasattr(plan.trigger, 'value') else str(plan.trigger)}",
        f"Total Jobs: {len(plan.jobs)}",
        f"Estimated Runtime: {plan.estimated_runtime_seconds or 0:.1f}s",
        f"Estimated Memory: {plan.estimated_memory_mb or 0:.1f}MB",
        f"",
        f"Disclaimer: {plan.disclaimer}"
    ]
    return "\n".join(lines)

def format_batch_run_text(run: Any) -> str:
    lines = [
        f"Research Batch Run: {run.batch_id}",
        f"Status: {run.status.value if hasattr(run.status, 'value') else str(run.status)}",
        f"Total Jobs: {len(run.jobs)}",
        f"Success: {run.success_count}, Failed: {run.failed_count}, Skipped: {run.skipped_count}",
        f"Elapsed Time: {run.elapsed_seconds:.1f}s",
        f"",
        f"Disclaimer: {run.disclaimer}"
    ]
    return "\n".join(lines)

from bist_signal_bot.deployment.reporting import format_first_run_text, format_smoke_test_text, format_environment_doctor_text

# Factors CLI formatting will be registered here
