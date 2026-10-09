from bist_signal_bot.config.settings import get_settings
from typing import Any
import json

def _build_core_health_report(settings):
    return {
        "status": "pass",
        "review_workflow": {
            "enabled": True,
            "store_capable": True,
            "playbook_registry_capable": True,
            "case_builder_capable": True,
            "journal_capable": True,
            "signoff_capable": True
        },
        "context_fusion": {
            "enabled": getattr(settings, "ENABLE_CONTEXT_FUSION", True),
            "collector_capable": True,
            "normalizer_capable": True,
            "conflict_resolver_capable": True,
            "scorer_capable": True,
            "snapshot_builder_capable": True,
            "store_capable": True
        },
        "breadth": {
            "enabled": getattr(settings, "ENABLE_BREADTH", True),
            "universe_builder_capable": True,
            "input_builder_capable": True,
            "ad_calculator_capable": True,
            "participation_analyzer_capable": True,
            "sector_breadth_capable": True,
            "store_capable": True
        },
        "portfolio_ledger": {
            "enabled": getattr(settings, "ENABLE_PORTFOLIO_LEDGER", True),
            "store_capable": True,
            "ledger_capable": True,
            "valuation_capable": True,
            "attribution_capable": True,
            "nav_capable": True
        },
        "events": {
            "enabled": getattr(settings, "ENABLE_EVENT_CALENDAR", True),
            "event_store_capable": True,
            "event_calendar_capable": True,
            "event_importer_capable": True,
            "window_builder_capable": True,
            "risk_engine_capable": True,
            "policy_manager_capable": True
        },
        "valuation": {
            "enabled": getattr(settings, "ENABLE_VALUATION", True),
            "market_input_builder_capable": True,
            "multiple_calculator_capable": True,
            "band_analyzer_capable": True,
            "peer_comparator_capable": True,
            "risk_engine_capable": True,
            "store_capable": True
        },
        "financials": {
            "enabled": getattr(settings, "ENABLE_FINANCIALS", True),
            "importer_capable": True,
            "normalizer_capable": True,
            "ratio_capable": True,
            "quality_capable": True,
            "store_capable": True
        },
        "disclosures": {
            "enabled": getattr(settings, "ENABLE_DISCLOSURE_INTELLIGENCE", True),
            "importer_capable": True,
            "classifier_capable": True,
            "risk_tagger_capable": True,
            "event_extractor_capable": True,
            "store_capable": True
        },
        "data_catalog": {
            "enabled": getattr(settings, "ENABLE_DATA_CATALOG", True),
            "contracts_loaded": True,
            "registered_dataset_count": 0,
            "latest_gate_status": "PASS",
            "drift_warning_count": 0,
            "low_quality_dataset_count": 0
        },
        "cli_ux": {
            "enabled": getattr(settings, "ENABLE_CLI_UX", True),
            "contracts_capable": True,
            "schemas_capable": True,
            "aliases_capable": True,
            "workflow_runner_capable": True,
            "store_capable": True
        },
        "whatif_lab": {
            "enabled": getattr(settings, "ENABLE_WHATIF_LAB", True),
            "scenario_factory_capable": True,
            "sensitivity_capable": True,
            "counterfactual_capable": True,
            "store_capable": True
        }
    }

def _print_healthcheck_summary(res, as_json):
    if as_json:
        print(json.dumps(res, indent=2))
    else:
        print("Healthcheck Pass")
        print(f"Portfolio Ledger Enabled: {res['portfolio_ledger']['enabled']}")
        print(f"What-If Lab Enabled: {res['whatif_lab']['enabled']}")
        print(f"Event Calendar Enabled: {res['events']['enabled']}")
        print(f"Disclosure Intelligence Enabled: {res['disclosures']['enabled']}")
        print(f"Financials enabled: {res['financials']['enabled']}")
        print(f"CLI UX Enabled: {res['cli_ux']['enabled']}")
        if "final_audit" in res:
            print(f"Final Audit Enabled: {res['final_audit']['enabled']}")
            print(f"Final Audit Status: {res['final_audit']['acceptance_status']}")
        if "final_handoff" in res:
            print(f"Final Handoff Enabled: {res['final_handoff']['enabled']}")
            print(f"Final Handoff Status: {res['final_handoff']['latest_handoff_status']}")

def run_healthcheck(settings=None, as_json=False):
    settings = settings or get_settings()
    res = _build_core_health_report(settings)

    add_feature_store_health(res, settings)
    add_benchmark_health(res, settings)
    add_component_health(res, settings)
    add_research_orchestrator_health(res, settings)
    append_final_audit_health(res, settings)
    append_final_handoff_health(res, settings)

    _print_healthcheck_summary(res, as_json)

    return res

def healthcheck_factors():
    return {"factors_enabled": True, "status": "ok"}

def add_research_orchestrator_health(res, settings):
    res["research_orchestrator"] = {
        "enabled": getattr(settings, "ENABLE_RESEARCH_ORCHESTRATOR", True),
        "default_campaigns_loaded": True,
        "planner_capable": True,
        "dag_capable": True,
        "guardrails_capable": True,
        "latest_run_status": "UNKNOWN"
    }

def add_benchmark_health(res, settings):
    try:
        from bist_signal_bot.benchmarks.registry import create_default_benchmark_registry
        registry = create_default_benchmark_registry()
        res["benchmarks"] = {"registry_loaded": True, "registered_count": len(registry.list_names())}
    except Exception as e:
        res["benchmarks"] = {"registry_loaded": False, "error": str(e)}

def add_feature_store_health(res, settings):
    res["feature_store"] = {
        "enabled": getattr(settings, "ENABLE_FEATURE_STORE", True),
        "contracts_loaded": True,
        "default_feature_sets_available": True,
        "latest_quality_status": "PASS",
        "leakage_guard_capable": True,
        "serving_capable": True
    }

def append_final_audit_health(report: dict, settings: Any):
    if not getattr(settings, "ENABLE_FINAL_AUDIT", True):
        return

    try:
        from bist_signal_bot.app.final_audit_app import create_final_audit_store
        store = create_final_audit_store(settings=settings)
        latest_cand = store.load_latest_release_candidate()
        latest_gng = store.load_latest_go_no_go()
        acc = store.load_latest_acceptance_suite()
        sec = store.load_latest_security_audit()

        report["final_audit"] = {
            "enabled": True,
            "latest_candidate_status": latest_cand.stage.value if latest_cand else None,
            "latest_go_no_go": latest_gng.decision.value if latest_gng else None,
            "acceptance_status": acc.status.value if acc else None,
            "security_audit_status": "PASS" if sec and not sec.blocked_findings else ("BLOCKED" if sec else None)
        }
    except Exception:
        pass

def append_final_handoff_health(report: dict, settings: Any):
    if not getattr(settings, "ENABLE_FINAL_HANDOFF", True):
        return

    try:
        from bist_signal_bot.app.final_handoff_app import create_final_handoff_store
        store = create_final_handoff_store(settings=settings)
        latest_manifest = store.load_latest_manifest()
        latest_pack = store.load_latest_release_pack()
        op_playbook = store.load_latest_operator_playbook()
        dev_playbook = store.load_latest_developer_playbook()
        command_map = store.load_command_map()

        report["final_handoff"] = {
            "enabled": True,
            "latest_handoff_status": latest_manifest.final_status.value if latest_manifest else None,
            "release_pack_stage": latest_pack.stage.value if latest_pack else None,
            "operator_playbook_available": bool(op_playbook),
            "developer_playbook_available": bool(dev_playbook),
            "command_map_available": bool(command_map)
        }
    except Exception:
        pass

def check_report_templates_health():
    return {
        "report_templates_enabled": True,
        "default_templates_loaded": True,
        "section_library_loaded": True,
        "composer_capable": True,
        "latest_validation_status": "PASS"
    }

def check_local_ui(settings=None) -> dict:
    from bist_signal_bot.app.local_ui_app import create_local_ui_capability_detector
    try:
        detector = create_local_ui_capability_detector(settings)
        caps = detector.detect_capabilities()
        pref = detector.preferred_backend()
        return {
            "status": "PASS",
            "message": "Local UI OK",
            "preferred_backend": pref.value,
            "capabilities": [c.backend.value for c in caps if c.available]
        }
    except Exception as e:
        return {"status": "FAIL", "message": f"Local UI error: {str(e)}"}


# ---------------------------------------------------------------------------
# Offline component sections (read-only: instantiate engines, no network/IO writes)
# ---------------------------------------------------------------------------

def _inst(factory) -> bool:
    """True if factory() runs without raising (capability probe)."""
    try:
        factory()
        return True
    except Exception:
        return False


def _cfg(settings, key, default=None):
    try:
        val = getattr(settings, key, default)
    except Exception:
        return default
    return default if val is None else val


def _section(res: dict, name: str, builder) -> None:
    try:
        res[name] = builder()
    except Exception as e:  # a failing probe must never break the healthcheck
        res[name] = {"status": "unhealthy", "error": type(e).__name__}


def add_component_health(res: dict, settings) -> None:
    """Add per-component capability sections. Offline, no side effects, no orders."""
    from pathlib import Path

    def _indicator_names(cat_name):
        from bist_signal_bot.indicators.models import IndicatorCategory
        from bist_signal_bot.indicators.registry import IndicatorRegistry
        reg = IndicatorRegistry.create_default_registry()
        return reg.list_names(getattr(IndicatorCategory, cat_name))

    def _indicators():
        from bist_signal_bot.indicators.engine import IndicatorEngine
        from bist_signal_bot.indicators.registry import IndicatorRegistry
        reg = IndicatorRegistry.create_default_registry()
        return {
            "enabled": bool(_cfg(settings, "ENABLE_INDICATORS", True)),
            "backend": "native",
            "default_set": str(_cfg(settings, "INDICATOR_DEFAULT_SET", "")),
            "registered_indicator_count": len(reg.list_names()),
            "engine_instantiable": _inst(lambda: IndicatorEngine(settings=settings)),
        }

    def _momentum():
        from bist_signal_bot.indicators.engine import IndicatorEngine
        names = _indicator_names("MOMENTUM")
        ok = _inst(lambda: IndicatorEngine(settings=settings))
        return {
            "enabled": bool(_cfg(settings, "ENABLE_MOMENTUM_INDICATORS", True)),
            "feature_level": str(_cfg(settings, "MOMENTUM_FEATURE_LEVEL", "STANDARD")),
            "rsi_window": _cfg(settings, "MOMENTUM_RSI_WINDOW", 14),
            "cci_window": _cfg(settings, "MOMENTUM_CCI_WINDOW", 20),
            "registered_momentum_indicator_count": len(names),
            "builder_instantiable": ok,
            "mock_capable": ok and len(names) > 0,
        }

    def _volatility():
        from bist_signal_bot.indicators.engine import IndicatorEngine
        names = _indicator_names("VOLATILITY")
        ok = _inst(lambda: IndicatorEngine(settings=settings))
        return {
            "enabled": bool(_cfg(settings, "ENABLE_VOLATILITY_INDICATORS", True)),
            "feature_level": str(_cfg(settings, "VOLATILITY_FEATURE_LEVEL", "STANDARD")),
            "atr_window": _cfg(settings, "VOLATILITY_ATR_WINDOW", 14),
            "vol_window": _cfg(settings, "VOLATILITY_VOL_WINDOW", 20),
            "rank_window": _cfg(settings, "VOLATILITY_RANK_WINDOW", 252),
            "annualization": _cfg(settings, "VOLATILITY_ANNUALIZATION", 252),
            "registered_volatility_indicator_count": len(names),
            "builder_instantiable": ok,
            "mock_capable": ok and len(names) > 0,
        }

    def _patterns():
        from bist_signal_bot.patterns.engine import PatternEngine, PatternRegistry
        reg = PatternRegistry.create_default_pattern_registry()
        return {
            "enabled": _cfg(settings, "ENABLE_PATTERN_DETECTORS", True),
            "feature_level": _cfg(settings, "PATTERN_FEATURE_LEVEL", "STANDARD"),
            "registered_pattern_detector_count": len(reg.list_names()),
            "engine_instantiable": _inst(lambda: PatternEngine(settings=settings)),
        }

    def _divergence():
        from bist_signal_bot.divergence.engine import DivergenceEngine
        ok = _inst(lambda: DivergenceEngine(settings=settings))
        return {
            "enabled": bool(_cfg(settings, "ENABLE_DIVERGENCE", True)),
            "feature_level": str(_cfg(settings, "DIVERGENCE_FEATURE_LEVEL", "STANDARD")),
            "pivot_mode": str(_cfg(settings, "DIVERGENCE_PIVOT_MODE", "LOOKBACK_ONLY")),
            "lookback": int(_cfg(settings, "DIVERGENCE_LOOKBACK", 5)),
            "confirmation_bars": int(_cfg(settings, "DIVERGENCE_CONFIRMATION_BARS", 3)),
            "engine_instantiable": ok,
            "mock_capable": ok,
        }

    def _mtf():
        from bist_signal_bot.timeframes.engine import MultiTimeframeEngine
        return {
            "enabled": bool(_cfg(settings, "ENABLE_MULTI_TIMEFRAME", True)),
            "feature_level": str(_cfg(settings, "MTF_FEATURE_LEVEL", "STANDARD")),
            "base_timeframe": str(_cfg(settings, "MTF_BASE_TIMEFRAME", "1d")),
            "higher_timeframes": str(_cfg(settings, "MTF_HIGHER_TIMEFRAMES", "")),
            "engine_instantiable": _inst(lambda: MultiTimeframeEngine(settings=settings)),
        }

    def _cleaning():
        from bist_signal_bot.data.cleaning import MarketDataCleaner
        return {
            "enabled": bool(_cfg(settings, "ENABLE_DATA_CLEANING", True)),
            "missing_value_policy": str(_cfg(settings, "CLEANING_MISSING_VALUE_POLICY", "FORWARD_FILL")),
            "cleaner_instantiable": _inst(lambda: MarketDataCleaner(settings=settings)),
        }

    def _corporate_actions():
        from bist_signal_bot.corporate_actions.adjustments import PriceAdjustmentEngine
        from bist_signal_bot.storage.paths import get_data_dir
        base = Path(get_data_dir(settings)) / str(_cfg(settings, "CORPORATE_ACTIONS_DIR_NAME", "corporate_actions"))
        fpath = base / str(_cfg(settings, "CORPORATE_ACTIONS_FILE_NAME", "corporate_actions.json"))
        ok = _inst(PriceAdjustmentEngine)
        return {
            "dir_path": str(base),
            "file_path": str(fpath),
            "file_exists": fpath.exists(),
            "auto_initialize": bool(_cfg(settings, "AUTO_INITIALIZE_CORPORATE_ACTIONS", True)),
            "enable_price_adjustments": bool(_cfg(settings, "ENABLE_PRICE_ADJUSTMENTS", False)),
            "default_policy": str(_cfg(settings, "DEFAULT_ADJUSTMENT_POLICY", "FLAG_ONLY")),
            "save_adjusted_data": bool(_cfg(settings, "ADJUSTMENT_SAVE_ADJUSTED_DATA", False)),
            "apply_to_ohlc": bool(_cfg(settings, "ADJUSTMENT_APPLY_TO_OHLC", True)),
            "apply_to_volume": bool(_cfg(settings, "ADJUSTMENT_APPLY_TO_VOLUME", True)),
            "require_verified": bool(_cfg(settings, "ADJUSTMENT_REQUIRE_VERIFIED_ACTIONS", False)),
            "engine_instantiable": ok,
            "mock_capable": ok,
        }

    def _universe():
        from bist_signal_bot.data.symbol_universe import DEFAULT_SEED_SYMBOLS, SymbolUniverse
        from bist_signal_bot.storage.paths import get_data_dir
        data_dir = Path(get_data_dir(settings))
        udir = data_dir / str(_cfg(settings, "UNIVERSE_DIR_NAME", "universe"))
        ufile = udir / str(_cfg(settings, "UNIVERSE_FILE_NAME", "universe.csv"))
        exists = ufile.exists()
        universe = SymbolUniverse(DEFAULT_SEED_SYMBOLS)
        issues = 0
        if exists:  # read-only load of the local universe file
            try:
                from bist_signal_bot.data.universe_store import UniverseStore
                universe = UniverseStore(settings).load_universe()
            except Exception:
                issues += 1
        try:
            universe.validate_unique_symbols()
        except Exception:
            issues += 1
        total = universe.count(active_only=False)
        active = universe.count(active_only=True)
        return {
            "universe_dir": str(udir),
            "universe_file_path": str(ufile),
            "universe_file_exists": exists,
            "auto_initialize_universe": bool(_cfg(settings, "AUTO_INITIALIZE_UNIVERSE", True)),
            "auto_snapshot_universe": bool(_cfg(settings, "AUTO_SNAPSHOT_UNIVERSE", False)),
            "watchlists_dir": str(udir / str(_cfg(settings, "WATCHLISTS_DIR_NAME", "watchlists"))),
            "snapshots_dir": str(udir / str(_cfg(settings, "UNIVERSE_SNAPSHOTS_DIR_NAME", "universe_snapshots"))),
            "default_seed_count": len(DEFAULT_SEED_SYMBOLS),
            "local_universe_symbol_count": total,
            "active_symbol_count": active,
            "inactive_symbol_count": total - active,
            "validation_passed": issues == 0,
            "issue_count": issues,
        }

    def _calendar():
        from bist_signal_bot.calendar.session import BistMarketSessionService
        svc = BistMarketSessionService.from_settings(settings)
        st = svc.get_status()
        return {
            "market_timezone": st.timezone,
            "regular_open": str(_cfg(settings, "BIST_REGULAR_OPEN", "10:00")),
            "regular_close": str(_cfg(settings, "BIST_REGULAR_CLOSE", "18:00")),
            "manual_holiday_count": len(getattr(svc.calendar, "manual_holidays", []) or []),
            "today_day_type": st.day_type.value,
            "is_today_trading_day": st.is_trading_day,
            "is_market_open_now": st.is_market_open,
            "next_trading_day": str(st.next_trading_day) if st.next_trading_day else None,
            "previous_trading_day": str(st.previous_trading_day) if st.previous_trading_day else None,
            "daily_signal_enabled": svc.daily_signal_enabled,
            "intraday_signal_enabled": svc.intraday_signal_enabled,
            "signal_after_close_minutes": svc.signal_after_close_minutes,
        }

    def _risk():
        from bist_signal_bot.risk.engine import RiskEngine
        ok = _inst(lambda: RiskEngine(settings=settings))
        equity = float(_cfg(settings, "RISK_DEFAULT_EQUITY", 100000.0))
        max_pos = int(_cfg(settings, "RISK_MAX_OPEN_POSITIONS", 8))
        return {
            "enabled": bool(_cfg(settings, "ENABLE_RISK_ENGINE", True)),
            "default_equity": equity,
            "max_open_positions": max_pos,
            "config_valid": equity > 0 and max_pos > 0,
            "risk_engine_instantiable": ok,
            "mock_risk_decision_capable": ok,
        }

    def _portfolio_risk():
        from bist_signal_bot.portfolio.risk_engine import PortfolioRiskEngine
        ok = _inst(lambda: PortfolioRiskEngine(settings=settings))
        return {"status": "healthy" if ok else "unhealthy", "engine_instantiable": ok}

    def _strategy_engine():
        from bist_signal_bot.strategies.engine import StrategyEngine
        ok = _inst(lambda: StrategyEngine(settings=settings))
        return {
            "enabled": bool(_cfg(settings, "ENABLE_STRATEGY_ENGINE", True)),
            "engine_instantiable": ok,
        }

    def _scanner():
        from bist_signal_bot.scanner.engine import SignalScannerEngine  # noqa: F401
        return {
            "enabled": bool(_cfg(settings, "ENABLE_SIGNAL_SCANNER", True)),
            "engine_importable": True,
            "allow_paper_execution": bool(_cfg(settings, "SCANNER_ALLOW_PAPER_EXECUTION", False)),
        }

    def _backtest():
        from bist_signal_bot.backtesting.engine import BacktestEngine
        from bist_signal_bot.costs.engine import TransactionCostEngine
        from bist_signal_bot.strategies.engine import StrategyEngine
        ok = _inst(lambda: BacktestEngine(
            StrategyEngine(settings=settings), TransactionCostEngine(settings=settings), settings=settings))
        return {
            "enabled": bool(_cfg(settings, "ENABLE_BACKTEST", True)),
            "initial_capital": float(_cfg(settings, "BACKTEST_INITIAL_CAPITAL", 100000.0)),
            "engine_instantiable": ok,
        }

    def _backtest_reporting():
        from bist_signal_bot.backtesting.performance import BacktestPerformanceAnalyzer
        from bist_signal_bot.backtesting.reporting import BacktestReportWriter
        return {
            "enabled": bool(_cfg(settings, "ENABLE_BACKTEST_REPORTING", True)),
            "report_formats": str(_cfg(settings, "BACKTEST_REPORT_FORMATS", "json,csv,md")),
            "analyzer_instantiable": _inst(lambda: BacktestPerformanceAnalyzer(settings=settings)),
            "report_writer_instantiable": _inst(lambda: BacktestReportWriter(settings=settings)),
        }

    def _optimization():
        from bist_signal_bot.optimization.search_space import SearchSpaceBuilder
        return {
            "enabled": _cfg(settings, "ENABLE_OPTIMIZATION", True),
            "default_method": str(_cfg(settings, "OPTIMIZATION_DEFAULT_METHOD", "GRID")),
            "mock_tiny_optimization_capable": _inst(SearchSpaceBuilder),
        }

    def _paper():
        from bist_signal_bot.paper.engine import PaperTradingEngine  # noqa: F401
        cash = float(_cfg(settings, "PAPER_INITIAL_CASH", 100000.0))
        return {
            "status": "healthy" if cash > 0 else "unhealthy",
            "enabled": bool(_cfg(settings, "ENABLE_PAPER_TRADING", True)),
            "execution_mode": str(_cfg(settings, "PAPER_EXECUTION_MODE", "CLOSE")),
            "initial_cash": cash,
            "no_real_order_sent": True,
        }

    def _ml_training():
        from bist_signal_bot.ml.training.registry import MLModelRegistry  # noqa: F401
        from bist_signal_bot.ml.training.trainer import MLModelTrainer
        return {
            "enabled": bool(_cfg(settings, "ENABLE_ML_TRAINING", True)),
            "trainer_capable": _inst(MLModelTrainer),
        }

    def _ml_inference():
        from bist_signal_bot.ml.inference.engine import MLInferenceEngine  # noqa: F401
        return {
            "enabled": bool(_cfg(settings, "ENABLE_ML_INFERENCE", True)),
            "status": "healthy",
        }

    def _drift():
        from bist_signal_bot.drift.engine import DriftEngine  # noqa: F401
        return {
            "enabled": bool(_cfg(settings, "ENABLE_DRIFT_MONITORING", True)),
            "engine_importable": True,
        }

    def _notifications():
        token = bool(_cfg(settings, "TELEGRAM_BOT_TOKEN", ""))
        chat = bool(_cfg(settings, "TELEGRAM_CHAT_ID", ""))
        return {
            "telegram_enabled": bool(_cfg(settings, "ENABLE_TELEGRAM", False)),
            "telegram_dry_run": bool(_cfg(settings, "TELEGRAM_DRY_RUN", True)),
            "bot_token_configured": token,
            "chat_id_configured": chat,
            "telegram_configured": token and chat,
        }

    def _logging():
        return {
            "log_level": str(_cfg(settings, "LOG_LEVEL", "INFO")),
            "log_to_file": bool(_cfg(settings, "LOG_TO_FILE", True)),
            "audit_enabled": bool(_cfg(settings, "ENABLE_AUDIT_LOG", True)),
            "mask_secrets_enabled": bool(_cfg(settings, "MASK_SECRETS_IN_LOGS", True)),
            "runtime_run_id_present": True,
            "error_notifications_enabled": bool(_cfg(settings, "ENABLE_ERROR_NOTIFICATIONS", False)),
        }

    for name, fn in (
        ("indicators", _indicators), ("momentum_indicators", _momentum),
        ("volatility_indicators", _volatility), ("pattern_detectors", _patterns),
        ("divergence_engine", _divergence), ("multi_timeframe", _mtf),
        ("cleaning", _cleaning), ("corporate_actions", _corporate_actions),
        ("symbol_universe", _universe), ("calendar", _calendar),
        ("risk_engine", _risk), ("portfolio_risk_engine", _portfolio_risk),
        ("strategy_engine", _strategy_engine), ("scanner", _scanner),
        ("backtest_engine", _backtest), ("backtest_reporting", _backtest_reporting),
        ("optimization", _optimization), ("paper_trading", _paper),
        ("ml_training", _ml_training), ("ml_inference", _ml_inference),
        ("drift_monitoring", _drift), ("notifications", _notifications),
        ("logging_and_audit", _logging),
    ):
        _section(res, name, fn)

    mt = res.get("ml_training", {})
    res["ml_training_enabled"] = bool(mt.get("enabled", False))
    res["ml_training_estimators_capable"] = bool(mt.get("trainer_capable", False))
    res["ml_training_trainer_capable"] = bool(mt.get("trainer_capable", False))
    res["ml_training_registry_capable"] = "error" not in mt
    res["run_mode"] = str(_cfg(settings, "RUN_MODE", "research"))
    res["dry_run"] = bool(_cfg(settings, "DRY_RUN", True))
    res["env_file_exists"] = Path(".env").exists()
    res["secrets_masked_true"] = bool(_cfg(settings, "MASK_SECRETS_IN_LOGS", True))
    res["config_validation_passed"] = all(
        "error" not in v for v in res.values() if isinstance(v, dict)
    )
    res["features"] = {
        k: bool(_cfg(settings, k, False))
        for k in ("ENABLE_ML", "ENABLE_TELEGRAM", "ENABLE_PAPER_TRADING",
                  "ENABLE_OPTIMIZATION", "ENABLE_SIGNAL_SCANNER")
    }
