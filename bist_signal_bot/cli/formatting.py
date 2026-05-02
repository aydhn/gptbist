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
