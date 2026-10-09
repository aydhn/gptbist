# Module map (on-demand reference)

Not auto-loaded. Read only when a task touches one of these packages. Source: skim of `bist_signal_bot/*`
(class/export level, not every module body). Verify before relying on a "gotcha". Convention: most research
layers = `*Store` (persistence) + `*Engine`/`*Builder`/`*Manager`. `app/*_app.py` (~65) are thin wiring/bootstraps.

## Core pipeline (live)
- `core/` shared utils: `time_utils` (utc_now, istanbul_now), `safety` (`assert_no_forbidden_trading_claims`), `audit` (`AuditLogger`), `exceptions`, `logging_setup`.
- `config/` `settings.py`, `defaults.py`; `config_registry/` snapshots/flags/FORBIDDEN keys (`schema.py`).
- `data/` `MarketDataService` (data_service.py); `data_catalog/` quality gates; `data_import/` schema mapping; `calendar/`, `scheduler/`, `markets/`, `timeframes/` sessions & calendars.
- `indicators/` `IndicatorEngine`; `features/` per-family `*FeatureBuilder`; `feature_store/`; `patterns/` `PatternEngine`; `breadth/` `BreadthEngine`; `divergence/`.
- `strategies/`, `strategy_registry/`, `signals/` (`SignalLifecycleManager`), `scanner/` (`SignalScannerEngine`).
- `risk/` (`RiskEngine`, `RiskFilterEngine`), `portfolio/` (`PortfolioRiskEngine`), `portfolio_construction/` (half-wired), `costs/` (`TransactionCostEngine`).
- `backtesting/` `BacktestEngine`; `validation/` `StrategyValidationEngine`; `optimization/` (grid/random/walk-forward); `monte_carlo/`, `stress/`, `whatif/`, `scenarios/`.
- `paper/` `PaperAccountManager` (paper only); `execution_sim/`; `portfolio_ledger/`, `valuation/`.
- `regime/` `RegimeEngine` (live; used by app/runtime_app and ml).
- `ml/` dataset builder, feature builder, `training/trainer.py`; `model_registry/`; `calibration/`; `ensemble/`; `drift/` `DriftEngine`; `adaptive/` `AdaptiveEngine`.
- `runtime/` `RuntimeOrchestrator`; `security/` `SecurityPreflightRunner`, `KillSwitchManager`; `monitoring/`; `telegram_center/`, `notifications/`.

## Research / governance / release layers (mostly reporting; check wiring before extending)
`research`, `research_lab`, `research_orchestrator`, `review`, `review_workflow`, `reports`, `report_templates`,
`knowledge`, `leaderboard`, `explainability`, `context_fusion`, `factors`, `fundamentals`, `financials`, `macro`,
`events`, `disclosures`, `governance`, `release`, `release_policy`, `final_audit`, `final_handoff`, `packaging`,
`deployment`, `maintenance`, `maintenance_automation`, `ops`, `qa`, `quality`, `plugins`, `local_ui`, `docs`, `docs_hub`,
`bootstrap` (`OfflineDemoRunner` demo.py), `performance`, `benchmarks`, `synthetic_scenarios`, `portfolio_research`, `storage`.

## CLI
`cli/main.py:run_cli` is the entry. Mostly argparse (`add_parser` ~800x across `cli/*_cli.py`/`*_commands.py`); typer is
mixed in `cli/commands.py` and `cli/validation_commands.py`. Routing: `cli/routers/dispatchers.py` (lazy imports in main.py).
A command may exist in only one framework: grep `add_parser`/`@app.command` to confirm.

## Tests
`bist_signal_bot/tests/` flat, ~990 `test_*.py` named by feature, a few subfolders (e.g. `tests/signals/`). `tests/conftest.py` (seed, `tmp_data_dir`, `settings_factory`); other
fixtures are per-file; shared helpers in `qa/fixtures.py`, `scenarios/fixtures.py`. `testpaths` set in `pyproject.toml`.

## Verified gotchas / dead code
- Removed (proven unreferenced): `regimes/`, `*_patch.py`, `docs/troubleshooting.py`, `app/{maintenance_automation,docs_hub}_app.py`; `core/exceptions.py` now has one `BistSignalBotError` base.
- `release/checks.py` references `"bist_signal_bot.regime"` by string; renaming that package breaks it silently.
- Duplicate names across packages: `PriceAdjustmentEngine` (`corporate_actions/` and `data/adjustments.py`), `CorporateActionStore`; troubleshooting builders in `docs/` and `docs_hub/`.
- Overlaps (unverified wiring): `portfolio` vs `portfolio_construction`; `maintenance` vs `maintenance_automation` vs `ops` backup/restore; `report_templates` vs `reports`; `research*` trio; `review` vs `review_workflow`; `adaptive` refresh planners (`model_refresh.py` vs `refresh_planner.py`); `backtesting/reports.py` vs `reporting.py`.
- `ml/base_model.py`: abstract train/predict, no concrete model there (training lives in `ml/training/trainer.py`).
- `monitoring/self_healing.py` can act on the system; review before relying on it.
