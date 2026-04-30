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
