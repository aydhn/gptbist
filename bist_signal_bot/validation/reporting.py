import pandas as pd
from typing import List, Dict, Any

from bist_signal_bot.validation.models import (
    WalkForwardResult, StrategyValidationResult
)

def walk_forward_to_dict(result: WalkForwardResult) -> Dict[str, Any]:
    return result.model_dump()

def format_validation_report_markdown(result: StrategyValidationResult) -> str:
    md = f"# Strategy Validation Report: {result.request.strategy_name}\n\n"
    md += f"**Status:** {result.status.value}\n"
    md += f"**Score:** {result.aggregate_score}\n"
    return md
