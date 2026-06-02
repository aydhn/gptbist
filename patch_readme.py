from pathlib import Path

readme_path = Path("README.md")
if readme_path.exists():
    content = readme_path.read_text()
    if "## Data Import" not in content:
        content += """

## Data Import

The local data import subsystem allows safe, offline parsing of various datasets (OHLCV, financials, macro, etc.) from CSV, JSON, JSONL, Parquet, and SQLite.

- **Preview & Mapping:** Generates schema mappings with confidence scores before any changes.
- **Validation:** Enforces strict offline checks against formats, missing columns, and path traversal risks.
- **Normalization:** Cleans dates, standardizes symbols, deduplicates rows, and manages decimal separators automatically.
- **Chunking:** Efficiently processes large files in chunks, without exhausting memory.
- **Dry-run First:** All import operations default to dry-run; writing to disk requires explicit confirmation (`--confirm`).

Usage examples:
```bash
python -m bist_signal_bot data-import preview --path data/my_ohlcv.csv --type OHLCV
python -m bist_signal_bot data-import map --path data/my_ohlcv.csv --type OHLCV
python -m bist_signal_bot data-import normalize --path data/my_ohlcv.csv --type OHLCV --dry-run
python -m bist_signal_bot data-import run --path data/my_ohlcv.csv --type OHLCV --confirm
```
"""
        readme_path.write_text(content)
