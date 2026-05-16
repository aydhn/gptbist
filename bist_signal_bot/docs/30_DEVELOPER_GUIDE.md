
### Phase 47: Research Ledger & Attribution

The `research` package provides an append-only JSONL storage (`ResearchStore` and `ResearchLedger`) and event tracking infrastructure (`SignalJournal`) to persist every significant research operation across the bot (backtests, optimizations, signal scans, paper trading, ML, regime detection, adaptive).

**Key Principles:**
- **Local Only:** No external tracking platforms (no MLflow, W&B, etc.).
- **Append-Only:** Historical edits (e.g. status changes, tag adding, journal outcome updating) write a new record or append metadata rather than deleting old ones, keeping full auditability (notes can be physically cleared to comply with privacy/security deletes, but with explicit confirmation).
- **Disclaimer Enforcement:** All output reports explicitly disclaim financial guarantees and mark themselves as research-only to comply with the project constraints.
- **Lineage:** Links between runs (like an Optimization run triggering an Adaptive Recommendation triggering a Runtime run) are tracked via `ResearchLineageResolver`.
- **Comparison & Attribution:** Provides tools (`ResearchComparator`, `ResearchAttributionEngine`) to group, rank, and summarize the journal outcomes and ledger runs by Symbol, Strategy, Regime, ML buckets, etc.
- **CLI Management:** `python -m bist_signal_bot research [log|list|show|compare|attribution|journal|note|outcome|lineage|export]`

## Reports Layer (Phase 48)

The Reports layer aggregates scanner, ML, risk, and runtime data into structured daily/weekly reports.
It handles formatting into Markdown, JSON, CSV, HTML, and optional PDF.
The digest module securely outputs short summaries to Telegram without financial claims or investment advice.
