# BIST Signal Bot

The **BIST Signal Bot** is a local-first, research-only algorithmic signal generator for Borsa Istanbul (BIST). It provides deterministic offline analysis, signal scanning, risk evaluation, and portfolio construction capabilities.

## 1. Project Summary

The system orchestrates multi-layer research components spanning data ingestion, feature stores, ML filters, factor scoring, strategy evaluation, and governance gating. It is explicitly designed for high-fidelity offline execution and metadata extraction.

## 2. Security Boundaries

- **Local Files Only**: Data is processed and saved entirely to local disk via JSONL/CSV.
- **No Cloud Services**: OpenAI APIs, external LLMs, or paid cloud APIs are strictly forbidden.
- **No HTML Scraping**: Web scraping (Selenium, Playwright, BeautifulSoup) is forbidden to maintain data stability.
- **Strict Configuration**: Secrets and paths are protected via `PathGuard` and secret redaction.

## 3. Research-Only & No-Real-Order Approach

**DISCLAIMER**: The software generates research metadata and simulated outcomes only. It is not investment advice or a recommendation to trade.

The application architecture includes a strict segregation between signal calculation and execution simulation. The core requirement is that **no real broker API connection is made, and no actual market orders are ever routed or sent.**

## 4. Quick Installation

Ensure you have Python 3.11+.

```bash
git clone <repository>
cd bist-signal-bot
pip install -r requirements.txt
cp .env.example .env
# Edit .env appropriately (ensure ENABLE_FINAL_HANDOFF=true)
```

## 5. Offline Demo

Run the local offline demonstration to verify your environment without any real data:

```bash
python -m bist_signal_bot bootstrap demo
```

## 6. Core Modules

The bot is composed of ~30 isolated modules including:
- **Data & Intelligence**: Data Catalog, Feature Store, Disclosures, Macro.
- **Research & Strategy**: Strategies, Factors, ML, Backtesting.
- **Operations & Governance**: Ops, QA, Final Audit, Research Orchestrator.
- **Final Handoff**: The capstone packaging and handover manifest layer.

## 7. CLI Command Map

Extensive functionality is exposed via the unified CLI. Run `python -m bist_signal_bot --help` to list commands. See `bist_signal_bot/docs/80_FINAL_COMMAND_MAP.md` for details.

## 8. Operator Daily Routine

Check system health, ops status, and generate daily reports:
```bash
python -m bist_signal_bot healthcheck --final-handoff
python -m bist_signal_bot ops staleness
python -m bist_signal_bot reports daily --dry-run
```

## 9. Developer Starting Point

Refer to `bist_signal_bot/docs/30_DEVELOPER_GUIDE.md` to see extension points, deterministic testing requirements, and coding conventions.

## 10. QA / Ops / Final Audit

Before any code updates, run the strict release and operational gates:
```bash
python -m bist_signal_bot qa release-gate --include-final-handoff
python -m bist_signal_bot ops readiness --include-final-handoff
python -m bist_signal_bot final-audit run
```

## 11. Final Handoff (Phase 100)

The Final Handoff layer bundles all current modules into deterministic release packs, playbooks, and reports indicating system readiness for research operations.

## 12. Known Limitations

- Single-machine execution only (no distributed computing).
- Data pipelines are daily/EOD resolution only.
- Strict isolation implies more manual coordination around dataset retention.

## 13. Roadmap

Post-release enhancements are tracked via the `python -m bist_signal_bot final-handoff roadmap` command. Core targets include performance optimization and richer data adapters.

## 14. Final MVP Closure Command Set

Validate your local MVP readiness with the following full-system run:

```bash
python -m bist_signal_bot bootstrap validate --profile STANDARD
python -m bist_signal_bot bootstrap demo --json
python -m bist_signal_bot healthcheck --bootstrap --ops --cli-ux --docs-hub --data-catalog --feature-store --model-registry --monitoring --leaderboard --orchestrator --final-audit --final-handoff
python -m bist_signal_bot qa release-gate --include-bootstrap --include-ops --include-cli-ux --include-docs-hub --include-data-catalog --include-feature-store --include-model-registry --include-monitoring --include-leaderboard --include-orchestrator --include-final-audit --include-final-handoff
python -m bist_signal_bot ops readiness --include-bootstrap --include-data-catalog --include-feature-store --include-model-registry --include-monitoring --include-leaderboard --include-orchestrator --include-final-audit --include-final-handoff
python -m bist_signal_bot orchestrator run --campaign QUICK_RESEARCH_SCAN --symbols ASELS THYAO --dry-run --json
python -m bist_signal_bot final-audit go-no-go --json
python -m bist_signal_bot final-handoff build --save --json
python -m bist_signal_bot final-handoff report --latest
pytest
```

## Performance Optimization
* Profiling
* Benchmark
* Resource budget
* Local cache
* Bottleneck analysis
* Regression checks
* QA/Ops integration
* CLI performance commands
