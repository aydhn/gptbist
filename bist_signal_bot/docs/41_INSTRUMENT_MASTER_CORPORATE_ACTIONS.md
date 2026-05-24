# Phase 69: Instrument Master & Corporate Actions

This layer provides a centralized and strictly offline record of all instruments in the BIST universe, managing symbol lifecycles, corporate actions, and adjusted OHLCV price series.

## Features
- **Instrument Master**: Maps symbols, ISINs, active status, sector, industry.
- **Symbol Lifecycle**: Tracks name changes, suspensions, delistings.
- **Corporate Actions**: Offline import of dividends, splits, mergers (CSV/JSON).
- **Price Adjustments**: Computes adjustment factors, creates 'adjusted OHLCV' without mutating 'raw OHLCV'.
- **Reconciliation**: Quality checks between data providers to detect missing/duplicate/zero bars.

## CLI Usage
```bash
python -m bist_signal_bot instruments list
python -m bist_signal_bot instruments show ASELS
python -m bist_signal_bot instruments import --file my_data.csv --confirm
python -m bist_signal_bot corporate-actions import --file my_ca.csv --confirm
python -m bist_signal_bot corporate-actions adjust ASELS --confirm
python -m bist_signal_bot data-quality check ASELS
```

## Security & Safety
- **No Web Scraping**: All data is imported locally.
- **No Execution**: Adjusted prices are metadata only, never sent to a broker.
