import os
from pathlib import Path

base_dir = Path("bist_signal_bot")

# 31. app/healthcheck.py update
health_path = base_dir / "app" / "healthcheck.py"
if health_path.exists():
    content = health_path.read_text()
    if "financials" not in content:
        import re
        content = re.sub(
            r'def run_healthcheck\(settings=None\):',
            r'''def run_healthcheck(settings=None):
    from bist_signal_bot.app.financials_app import (
        create_financial_store,
        create_financial_statement_importer,
        create_financial_statement_normalizer,
        create_financial_ratio_calculator,
        create_earnings_quality_analyzer
    )

    fin_enabled = getattr(settings, "ENABLE_FINANCIALS", True) if settings else True
    print(f"Financials enabled: {fin_enabled}")
    if fin_enabled:
        try:
            create_financial_store(settings)
            print("Financial store: Capable")
            create_financial_statement_importer(settings)
            print("Financial importer: Capable")
            create_financial_statement_normalizer(settings)
            print("Financial normalizer: Capable")
            create_financial_ratio_calculator(settings)
            print("Financial ratio calculator: Capable")
            create_earnings_quality_analyzer(settings)
            print("Financial quality analyzer: Capable")
        except Exception as e:
            print(f"Financials healthcheck failed: {e}")
''',
            content
        )
        health_path.write_text(content)

# 32. docs/53_FINANCIAL_STATEMENT_INTELLIGENCE.md
docs_path = base_dir / "docs" / "53_FINANCIAL_STATEMENT_INTELLIGENCE.md"
docs_path.parent.mkdir(parents=True, exist_ok=True)
docs_path.write_text('''# 53. FINANCIAL STATEMENT INTELLIGENCE

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
''')

# 33. update README.md
readme_path = Path("README.md")
if readme_path.exists():
    content = readme_path.read_text()
    if "Financial Statement Intelligence" not in content:
        content += '''
## Phase 81: Financial Statement Intelligence
Added offline financial statement normalization, ratio calculations, trend analysis, and earnings quality scoring via local CSV/JSON imports.
'''
        readme_path.write_text(content)

# 34. Generate tests that check the integration without making real calls
with open(base_dir / "tests" / "test_cli_financials.py", "w") as f:
    f.write('''import pytest
from unittest.mock import patch
from bist_signal_bot.cli.commands import run_financials_command

class DummyArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def test_cli_import_dry_run(capsys):
    args = DummyArgs(financials_command="import", file="test.csv", confirm=False, dry_run=True)
    with patch('bist_signal_bot.app.financials_app.create_financial_statement_importer') as mock_importer:
        mock_inst = mock_importer.return_value
        class MockRes:
            records_imported = 0
            records_skipped = 1
            duplicate_count = 0
        mock_inst.import_file.return_value = MockRes()

        run_financials_command(args)

        captured = capsys.readouterr()
        assert "Dry run complete." in captured.out

def test_cli_ratios_json(capsys):
    args = DummyArgs(financials_command="ratios", symbol="ASELS", json=True)
    run_financials_command(args)
    captured = capsys.readouterr()
    assert '"status": "ok"' in captured.out
    assert '"command": "ratios"' in captured.out
''')
