from typing import Any, Dict, Optional
from bist_signal_bot.config.settings import Settings

def check_scenarios(settings: Optional[Settings] = None) -> Dict[str, Any]:
    settings = settings or Settings()
    result = {
        "enabled": getattr(settings, "ENABLE_SCENARIO_RUNNER", True),
        "default_symbols": getattr(settings, "SCENARIO_DEFAULT_SYMBOLS", ""),
        "default_strategy": getattr(settings, "SCENARIO_DEFAULT_STRATEGY", ""),
        "sandbox_enabled": getattr(settings, "SCENARIO_USE_SANDBOX", True),
        "golden_enabled": getattr(settings, "SCENARIO_COMPARE_GOLDEN", False),
        "slow_step_threshold": getattr(settings, "SCENARIO_SLOW_STEP_SECONDS", 15.0),
    }

    try:
        from bist_signal_bot.scenarios.registry import ScenarioRegistry
        from bist_signal_bot.scenarios.validator import ScenarioValidator
        from bist_signal_bot.scenarios.golden import GoldenSnapshotManager
        from bist_signal_bot.app.scenarios_app import create_scenario_runner

        registry = ScenarioRegistry()
        result["registry_scenario_count"] = len(registry.list_scenarios())
        result["smoke_scenario_build_capable"] = registry.get_scenario("smoke") is not None

        # Test instantiation (without doing destructive actions or creating full dirs if possible)
        # Using a dummy base dir for safety in healthcheck
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdirname:
            runner = create_scenario_runner(settings, base_dir=Path(tmpdirname))
            result["scenario_runner_instantiable"] = runner is not None
            result["validator_capable"] = True
            result["golden_manager_capable"] = True

    except Exception as e:
        result["error"] = str(e)

    return result
