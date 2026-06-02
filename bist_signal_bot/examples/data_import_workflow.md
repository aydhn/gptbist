# Data Import Workflow Example

```bash
# 1. See what formats are available
python -m bist_signal_bot data-import formats

# 2. Preview data to ensure structure is recognized
python -m bist_signal_bot data-import preview --path data/raw/market_data.csv --type OHLCV

# 3. Check automatic schema mapping
python -m bist_signal_bot data-import map --path data/raw/market_data.csv --type OHLCV

# 4. Validate findings (missing columns, safe path, etc.)
python -m bist_signal_bot data-import validate --path data/raw/market_data.csv --type OHLCV

# 5. Run a dry-run import (no writes)
python -m bist_signal_bot data-import run --path data/raw/market_data.csv --type OHLCV --dry-run

# 6. Execute full import and register into catalog
python -m bist_signal_bot data-import run --path data/raw/market_data.csv --type OHLCV --confirm --save-catalog

# 7. Generate a report of recent jobs
python -m bist_signal_bot data-import report
```
