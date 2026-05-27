# 53. FINANCIAL STATEMENT INTELLIGENCE

## Overview
Phase 81 introduces the local-first Financial Statement Intelligence layer for BIST Signal Bot. This layer allows you to import raw financial statements (Income Statement, Balance Sheet, Cash Flow), normalize them, calculate deterministic ratios, analyze trends, and assess earnings quality—all completely offline.

## Core Principles
1. **Local Only**: All data is imported from local CSV/JSON files. No web scraping. No paid APIs.
2. **Deterministic**: Ratio and trend calculations are rule-based and deterministic.
3. **Research-Only**: Earnings quality scores and ratios do not predict future prices and are not investment advice.
4. **Offline Context**: Provides fundamental context to scanners, portfolios, and reviews without executing real market orders.

## Import Formats
Supports Wide CSV, Long CSV, and JSON formats.

Wide CSV example:
```csv
symbol,fiscal_year,fiscal_period,period_end,revenue,net_income,total_assets
ASELS,2024,Q4,2024-12-31,100,20,500
```

Long CSV example:
```csv
symbol,fiscal_year,fiscal_period,period_end,item_name,item_value
ASELS,2024,Q4,2024-12-31,revenue,100
ASELS,2024,Q4,2024-12-31,net_income,20
```

## CLI Usage
Import data:
`python -m bist_signal_bot financials import --file data/imports/financials.csv --confirm`

List imported data:
`python -m bist_signal_bot financials list --symbol ASELS`

Calculate ratios:
`python -m bist_signal_bot financials ratios ASELS`

## Metrics and Quality
- **Ratios**: Gross Margin, Operating Margin, EBITDA Margin, Net Margin, Debt/Equity.
- **Trends**: YoY and QoQ percentage changes.
- **Quality**: Cash Conversion Score (OCF / Net Income), Debt Quality Score.
