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

## Setup & tests

```bash
python -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt   # + scikit-learn for ML
.venv/Scripts/python -m pytest bist_signal_bot/tests/<area> -q
```

Runtime deps: pandas, numpy, pydantic, requests, yfinance, **typer**, **click**, joblib, scikit-learn,
python-dotenv. (`requirements.txt` and `pyproject.toml` are kept in sync.)

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

- **Portfolio construction is half-wired**: `portfolio_construction/engine.py` uses undefined
  `AllocationDecision`/`AllocationStatus` and `app/portfolio_construction_app.py` passes 10 ctor
  args the engine doesn't accept. Excluded from the demo until rebuilt.
- **getattr(settings, X, default)** sites (~700): because `Settings` always returns a value
  (never `AttributeError`), the caller's default is bypassed for unknown keys. Add such keys to
  `DEFAULTS` rather than relying on the inline default. Long-term: consider refining `__getattr__`.
- **Loop step coverage**: only HEALTHCHECK/SIGNAL_SCAN/PAPER_RUN/TELEGRAM_SUMMARY are executed in
  `_execute_pipeline_steps`; DATA_REFRESH/REGIME_ANALYSIS/ML_INFERENCE/CLEANUP are emitted as steps
  but not yet run. Wire these for full autonomy.
- ML filter & drift check are off by default (`RUNTIME_USE_ML_FILTER`, `RUNTIME_RUN_DRIFT_CHECK`)
  until a baseline model is trained and registered.

## Code style

Match surrounding code. Stdlib `logging` via `core/logging_setup.get_logger` (no loguru).
pydantic v2 models. Keep the no-real-order invariant in any new execution path.
See `docs/` (30 numbered guides) for deep dives; `docs/26_ARCHITECTURE.md` and `docs/30_DEVELOPER_GUIDE.md` first.
