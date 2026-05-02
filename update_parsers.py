import re

with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

new_parsers = """

    # patterns
    patterns_parser = subparsers.add_parser("patterns", help="Manage pattern detection")
    patterns_subparsers = patterns_parser.add_subparsers(dest="patterns_command", help="Pattern commands")

    # patterns list
    p_list_parser = patterns_subparsers.add_parser("list", help="List available patterns")
    p_list_parser.add_argument("--category", type=str, help="Filter by category (e.g. BREAKOUT, CANDLE)")
    p_list_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # patterns detect
    p_detect_parser = patterns_subparsers.add_parser("detect", help="Detect specific patterns on a symbol")
    p_detect_parser.add_argument("symbol", type=str, help="Symbol to process")
    p_detect_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    p_detect_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    p_detect_parser.add_argument("--rows", type=int, help="Mock data rows")
    p_detect_parser.add_argument("--pattern", type=str, action="append", help="Pattern to detect (e.g. price_breakout:window=20)")
    p_detect_parser.add_argument("--default-set", action="store_true", help="Run default pattern set")
    p_detect_parser.add_argument("--save-output", action="store_true", help="Save output to CSV")
    p_detect_parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # pattern-features
    pattern_features_parser = subparsers.add_parser("pattern-features", help="Generate pattern and price action features")
    pattern_features_parser.add_argument("symbol", type=str, help="Symbol to process")
    pattern_features_parser.add_argument("--source", type=str, choices=["local", "mock"], default="local", help="Data source")
    pattern_features_parser.add_argument("--timeframe", type=str, default="1d", help="Timeframe (e.g. 1d)")
    pattern_features_parser.add_argument("--rows", type=int, help="Mock data rows")
    pattern_features_parser.add_argument("--level", type=str, choices=["basic", "advanced", "full"], default="basic", help="Feature level")
    pattern_features_parser.add_argument("--save-output", action="store_true", help="Save output to CSV")
    pattern_features_parser.add_argument("--json", action="store_true", help="Output in JSON format")

"""

insertion_point = content.find("    # volume-features")
content = content[:insertion_point] + new_parsers + content[insertion_point:]

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.write(content)
