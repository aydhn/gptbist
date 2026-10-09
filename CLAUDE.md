# CLAUDE.md — BIST Signal Bot

Guidance for AI agents (and humans) working in this repo. Keep it current.

## What this is

A **local-first, research-only** algorithmic signal generator for Borsa İstanbul (BIST):
data ingestion → indicators → strategies → signal scanning → risk/portfolio evaluation →
ML filtering → backtesting/validation → an autonomous runtime loop that can adapt its own
parameters and retrain its own models. ~2100 Python modules, ~960 test files, ~550 CLI commands.

## ⚠️ Hard safety boundaries (never cross)

- **No real orders, ever.** No broker API connection, no order routing. `BROKER_ENABLED`,
  `REAL_ORDER_ENABLED`, `ENABLE_LIVE_TRADING` are `FORBIDDEN` in `config_registry/schema.py`.
  Every runtime result must carry "No real order sent." Trading is **paper/simulation only**.
- **Local files only.** No cloud services, no paid APIs, no LLM calls, no HTML scraping.
- Secrets live in `.env` (git-ignored). Never commit real secrets; `.env.example` is the template.

## Run commands

The single real CLI lives in `bist_signal_bot/cli/main.py:run_cli`. Both entry points delegate to it:

```bash
python -m bist_signal_bot <command> ...      # or: bist-signal-bot <command> ...
python -m bist_signal_bot version
python -m bist_signal_bot healthcheck
python -m bist_signal_bot bootstrap demo      # offline capability demo (safe)
python -m bist_signal_bot scan symbols ASELS THYAO --source local_file --strategy moving_average_trend
python -m bist_signal_bot runtime dry-run     # autonomous pipeline, no side effects
python -m bist_signal_bot runtime run-once    # one full pipeline iteration
python -m bist_signal_bot runtime loop        # continuous loop (RUNTIME_MAX_ITERATIONS / _SLEEP_SECONDS)
python -m bist_signal_bot runtime status      # persisted run state
```

Windows: `start_windows.bat` creates `.venv`, installs deps, runs healthcheck + the demo.

## Repo map (read on demand, not exhaustively)

`bist_signal_bot/` is the package (~100 subpackages: `cli/`, `config/`, `runtime/`, `adaptive/`, `ml/`,
`drift/`, `backtesting/`, `paper/`, `security/`, `tests/` mirrors the area names). `docs/` = 31 numbered guides +
`runbooks/` (incident playbooks: kill switch, stale data, quality gate failed, ...). `AGENTS.md` restates the
non-negotiables.
No `.venv` is checked in; create it first (see Setup).

Per-package entry points, test layout (shared `tests/conftest.py`: seed, `tmp_data_dir`, `settings_factory`), CLI framework split and
remaining verified duplicates (`PriceAdjustmentEngine` x2, `markets/calendar.py` vs `calendar/`) live in `docs/claude-context/module-map.md` — read it
only when touching those packages; it is not auto-loaded.

## Intraday data layer (`intraday/`)

SQLite bar archive (`archive.py`, raw bars, idempotent upsert, split actions, universe survivorship), rate-limited yfinance
fetcher + `ArchiveUpdater` (`fetcher.py`), BIST sessions/holidays/ticks/price limits (`sessions.py`, `bist_holidays.json` —
religious holidays unverified, confirm with Borsa Istanbul), gap/halt detection (`gaps.py`), freshness gate (`freshness.py`).
CLI: `python -m bist_signal_bot intraday archive-update|gaps|status`. Full BIST universe is synced dynamically from Yahoo's official screener (`universe_sync.py`, `universe sync [--dry-run]`;
`intraday archive-update --all-active` auto-syncs when `INTRADAY_UNIVERSE_AUTO_SYNC` and last sync >1 day; fail-closed if listing <
`INTRADAY_UNIVERSE_MIN_LISTING`; missing symbols deactivated only after `INTRADAY_UNIVERSE_DELIST_MISSES` syncs, seeds never dropped). Findings: `docs/claude-context/00-research-intraday.md`.

## Edge validation (`edge_validation/`)

Leak-free labels (`labels.py`), purged/embargoed K-Fold + CPCV + purged walk-forward (`cv.py`), DSR/PBO/BH/reality-check
(`stats.py`), BIST cost model (`costs.py`), append-only trial ledger counting every attempt (`ledger.py`), `CandidateGate`
(`gate.py`) and `runner.py`. CLI: `python -m bist_signal_bot edge run --family sma_trend --interval 1h [--placebo]`.
A strategy is a candidate only if the gate says CANDIDATE. Results so far: `docs/claude-context/01-edge-results.md`.

## Model loop (`model_loop/`)

`features.py` (causal intraday features), `training.py` (CPCV OOS eval, calibration, gate verdict, registers in
`model_registry`; non-CANDIDATE -> `WATCH` + warning, never auto-champion), `drift_monitor.py` (PSI, KS, ADWIN),
`lifecycle.py` (drift -> challenger -> compare -> `promote(confirm=True)` via preflight + kill switch + audit; rollback),
`runtime_guard.py` (RUNTIME_USE_ML_FILTER / RUNTIME_RUN_DRIFT_CHECK effective only when a baseline is registered; ML filter
additionally needs `RUNTIME_ML_MODEL_ID`). CLI: `python -m bist_signal_bot model-loop train|models|evaluate|promote|rollback|status`.
Tests that touch the real registry/data dir can change with local training state — prefer `tmp_data_dir`/`settings_factory`.

## Decision layer (`risk/`)

`sizing_intraday.py` (fractional Kelly w/ shrinkage + cap, vol targeting, risk budget, ADV/participation, lots, price-limit
awareness; `SizingDecision.method` = binding constraint), `portfolio_limits.py` (positions, gross, single-name, sector,
correlation cluster, daily turnover), `daily_loss.py` (`DailyLossGuard`: daily loss / consecutive losses / trailing drawdown
-> HALTED_FOR_DAY + PAPER kill switch + audit; drawdown/corrupt-state need `reset(confirm=True)`; fails closed),
`decision.py` (`DecisionLayer`: guard -> session/auction -> sizing -> limits -> edge-vs-cost; reduce-only exits bypass).
CLI: `python -m bist_signal_bot risk status|reset --confirm|simulate-day`. `RUNTIME_USE_DECISION_LAYER` (default False)
gates PAPER_RUN; per-order hooking is `paper/decision_hook.py::PaperDecisionHook`. `PaperTradingEngine.run(strategy_name, **kw)` is the
runtime adapter (point-in-time via `as_of`/`data_override`). `evidence/` (`replay_paper`, `compare_paper_backtest`; CLI
`python -m bist_signal_bot evidence ...`) reports paper-vs-backtest divergence to `data/evidence/`. No strategy/model has passed the edge gate yet.

## Setup & tests

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt pytest pytest-xdist pytest-timeout
.venv/Scripts/python -m pytest bist_signal_bot/tests/<area> -q
```

Runtime deps: pandas, numpy, pydantic, requests, yfinance, **typer**, **click**, joblib, scikit-learn,
python-dotenv, pyarrow, tabulate. (`requirements.txt` and `pyproject.toml` are kept in sync.)

## Configuration system (important)

`config/settings.py` is **not** pydantic-settings; it is a dependency-free loader with this precedence:

```
os.environ  >  .env  >  .env.example  >  config/defaults.py  >  name-based default
```

- Values are coerced to native types by **value form + key name** (bool/int/float/Path).
- `config/defaults.py::DEFAULTS` holds real values for the ~150+ keys the code reads directly
  but that are absent from `.env.example` (indicator windows, RISK_*, PORTFOLIO_*, RUNTIME_*,
  ADAPTIVE_* policy). Standard TA windows are used (RSI 14, long trend 200, etc.).
- `Settings()` and `get_settings()` are both supported; `.model_dump()`/`.dict()` aliases exist.
- **Never** reintroduce the old `__getattr__` → `"mock_value"` sentinel.

When a new engine needs a config key: add a typed default to `config/defaults.py` (don't rely on
the name-based fallback for type-critical numeric/bool keys).

## Autonomous loop

`runtime/orchestrator.py::RuntimeOrchestrator` is the loop. `app/runtime_app.py::create_runtime_orchestrator`
wires the scanner + paper engines (both need a shared `StrategyEngine`). Flow per iteration:
config gate → data freshness → adaptive config (`adaptive/engine.py`) → pipeline steps
(healthcheck, signal scan, regime, ML inference, paper, telegram) → drift check → report/notify →
audit + state persist. Security: `security/preflight.py`, `security/kill_switch.py`.

The learning pieces that make it "self-improving":
- `ml/training/trainer.py` — sklearn training (leakage guard, temporal split, model registry).
- `adaptive/engine.py` — recommends parameter/model refreshes; `apply_parameter_update(confirm=True)`
  applies them behind a security preflight + audit (`no_real_order_sent`).
- `drift/model_drift.py` — model/feature drift detection.

## Known gaps / follow-ups

- **Portfolio construction** was rebuilt (`construct`, `compare_methods`; ctor collaborators optional). Still excluded from the demo.
- **getattr(settings, X, default)**: `Settings` never raises `AttributeError`, so inline defaults are bypassed. ~330 such defaults were
  promoted to `DEFAULTS`; unknown `*_DIR_NAME` keys now derive `key minus suffix` (no stray `data/<key>_dir_name`). Add new keys to `DEFAULTS`.
- **Loop step coverage**: all steps (HEALTHCHECK, DATA_REFRESH, SIGNAL_SCAN, REGIME_ANALYSIS, ML_INFERENCE,
  PAPER_RUN, TELEGRAM_SUMMARY, CLEANUP) are dispatched in `_execute_pipeline_steps`
  (`runtime/orchestrator.py`); DATA_REFRESH feeds REGIME/ML/SIGNAL_SCAN via a shared `fetched_data` dict.
- ML filter & drift check are off by default (`RUNTIME_USE_ML_FILTER`, `RUNTIME_RUN_DRIFT_CHECK`)
  until a baseline model is trained and registered.
- **Backtest** test files are green (models/audit enum repaired). Test suite baseline (2026-10-10): 142 failed / 23 errors / 2813 passed (stale tests + stubbed modules, mostly healthcheck_*, optimization/leaderboard, remaining test_cli_*); no regressions allowed. Paper ledger credits idle-cash interest (`paper/cash_interest.py`, PAPER_CASH_INTEREST_ANNUAL/WITHHOLDING are unverified placeholders).
- **Audit metadata redaction**: `test_audit_logger_sanitizes_metadata` expects partial masking
  (`secr...6789`), but `SecretRedactor.redact_dict` does full `***REDACTED***` (stronger). The code
  is the safer behavior; treat the test as the stale side, not the code.

## Code style

Match surrounding code. Stdlib `logging` via `core/logging_setup.get_logger` (no loguru).
pydantic v2 models. Keep the no-real-order invariant in any new execution path.
See `docs/` (30 numbered guides) for deep dives; `docs/26_ARCHITECTURE.md` and `docs/30_DEVELOPER_GUIDE.md` first.
