import re

with open("bist_signal_bot/cli/formatting.py", "r") as f:
    content = f.read()

new_formatter = """

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

    return "\\n".join(lines)
"""

content += new_formatter

with open("bist_signal_bot/cli/formatting.py", "w") as f:
    f.write(content)
