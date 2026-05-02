import re

with open("README.md", "r") as f:
    content = f.read()

new_section = """
## Phase 21: Pattern, Breakout, and Price Action Feature Layer

Phase 21 introduces an extensive library of pattern detection components designed to extract robust technical features without look-ahead bias:
- **Candle Patterns**: Detects inside/outside bars, engulfing, doji, and hammer approximations.
- **Price Structure**: Detects rolling higher highs / lower lows, range position, and range compression.
- **Breakouts**: Identifies price breakouts, volume-confirmed breakouts, lagged false breakouts, and retests. To prevent data leakage, historical confirmation is rigorously applied to pseudo-future patterns like false breakouts.
- **Support & Resistance**: Dynamically tracks rolling SR levels and pivot points utilizing strict `shift(1)` isolation, avoiding baseline leakage.

This layer purely emits calculated features for backtesting and ML ingestion; it explicitly does **NOT** issue financial or trading advice. As per the strict requirements, there is no dashboard, HTML scraping, paid API integration, or real-order execution. Check out the available tools using `python -m bist_signal_bot patterns list` and `python -m bist_signal_bot pattern-features ASELS --source mock --level full`.
"""

content += new_section

with open("README.md", "w") as f:
    f.write(content)
