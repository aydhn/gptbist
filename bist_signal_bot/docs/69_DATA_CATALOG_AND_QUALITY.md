# Data Catalog & Data Quality (v1)

The Data Catalog acts as the central registry for all datasets used within the BIST Signal Bot.

## Overview
1. **Dataset Registry**: Discovers and registers local datasets, extracting formats and kinds (e.g. OHLCV, FINANCIALS, MACRO).
2. **Dataset Contracts**: Enforces schema contracts for each `DatasetKind`, ensuring datasets have the correct columns and structures before they're used by context or scanners.
3. **Dataset Profiler**: Evaluates local files (CSV, JSONL, Parquet) for shape, size, duplicates, null ratios, and basic value ranges.
4. **Data Quality Engine**: Evaluates dataset profiles against their contract, assigning scores and status flags (`PASS`, `WATCH`, `FAIL`, `BLOCKED`).
5. **Schema Drift Detector**: Warns if required columns go missing or new undocumented ones appear.
6. **Lineage & Provenance**: Tracks file checksums, source imports (yfinance vs manual CSV), and tracks the flow of data across systems.
7. **Quality Gates**: Integrates directly with QA release checks and Ops readiness checks. A blocked dataset will pause related actions if required by settings.

## Local Governance & Research-Only Rule
The system will never connect to external broker APIs, make execution decisions, or produce trading permission. It operates exclusively on local files (offline operation), analyzing structures and completeness for research. All reports output strict disclaimer messages indicating they are *local data reliability metadata only*.

## Commands
Use `python -m bist_signal_bot data-catalog` for all data catalog interactions. Examples:
- `data-catalog contracts`
- `data-catalog register --path data/imports/financials.csv --kind FINANCIALS`
- `data-catalog profile <dataset_id>`
- `data-catalog quality --all`
