
import pandas as pd
from typing import Any

def risk_decision_to_dict(decision) -> dict[str, Any]:
    return decision.summary()

def risk_batch_to_dataframe(batch) -> pd.DataFrame:
    return pd.DataFrame([d.summary() for d in batch.decisions])

def format_risk_decision_text(decision) -> str:
    lines = [
        f"--- Risk Decision for {decision.signal.symbol} ---",
        f"Strategy: {decision.signal.strategy_name}",
        f"Side: {decision.side.value}",
        f"Status: {decision.status.value}",
        f"Approved: {decision.approved}"
    ]
    if decision.position_size:
        ps = decision.position_size
        lines.append(f"Position Notional: {ps.final_notional}")
        lines.append(f"Quantity: {ps.quantity}")
        lines.append(f"Entry Price: {ps.entry_price}")
        if ps.stop_price: lines.append(f"Stop Price: {ps.stop_price}")

    if decision.stop_target and decision.stop_target.target_price:
        lines.append(f"Target Price: {decision.stop_target.target_price}")
        if decision.stop_target.risk_reward:
            lines.append(f"Risk/Reward: {decision.stop_target.risk_reward:.2f}")

    if decision.max_loss_amount:
        lines.append(f"Max Loss Amount: {decision.max_loss_amount}")

    if decision.estimated_total_cost:
        lines.append(f"Estimated Cost: {decision.estimated_total_cost}")

    if decision.filter_result.reject_reasons:
        reasons = [r.value for r in decision.filter_result.reject_reasons]
        lines.append(f"Reject Reasons: {', '.join(reasons)}")

    if decision.filter_result.warnings:
        lines.append(f"Warnings: {', '.join(decision.filter_result.warnings)}")

    lines.append(f"\nDisclaimer: {decision.disclaimer}")

    return "\n".join(lines)

def format_risk_batch_text(batch) -> str:
    return f"Batch Evaluated: {batch.requested_count}, Approved: {batch.approved_count}"
