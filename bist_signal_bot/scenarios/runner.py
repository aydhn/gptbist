import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.scenarios.models import ScenarioConfig, ScenarioResult, ScenarioStatus, ScenarioType
from bist_signal_bot.scenarios.fixtures import ScenarioFixtureBuilder
from bist_signal_bot.scenarios.steps import ScenarioStepExecutor
from bist_signal_bot.scenarios.registry import ScenarioRegistry
from bist_signal_bot.scenarios.golden import GoldenSnapshotManager
from bist_signal_bot.scenarios.validator import ScenarioValidator
from bist_signal_bot.scenarios.storage import ScenarioStore


@dataclass
class ScenarioRunnerDependencies:
    registry: Optional[ScenarioRegistry] = None
    fixture_builder: Optional[ScenarioFixtureBuilder] = None
    step_executor: Optional[ScenarioStepExecutor] = None
    golden_manager: Optional[GoldenSnapshotManager] = None
    validator: Optional[ScenarioValidator] = None
    storage: Optional[ScenarioStore] = None
    settings: Optional[Settings] = None
    logger: Optional[logging.Logger] = None

class ScenarioRunner:
    def __init__(
        self,
        deps: Optional[ScenarioRunnerDependencies] = None
    ):
        deps = deps or ScenarioRunnerDependencies()
        self.settings = deps.settings or Settings()
        self.logger = deps.logger or logging.getLogger(__name__)
        self.registry = deps.registry or ScenarioRegistry()
        self.fixture_builder = deps.fixture_builder or ScenarioFixtureBuilder()
        self.step_executor = deps.step_executor or ScenarioStepExecutor(settings=self.settings, logger=self.logger)
        self.storage = deps.storage or ScenarioStore(settings=self.settings)
        self.golden_manager = deps.golden_manager or GoldenSnapshotManager(golden_dir=self.storage.get_golden_dir())
        self.validator = deps.validator or ScenarioValidator(settings=self.settings)

    def run(self, scenario_id: str, update_golden: bool = False, compare_golden: Optional[bool] = None, save_outputs: bool = True, confirm_update_golden: bool = False) -> ScenarioResult:
        config = self.registry.get_scenario(scenario_id)
        if not config:
            raise ValueError(f"Scenario not found: {scenario_id}")

        config.update_golden = update_golden
        if compare_golden is not None:
             config.compare_golden = compare_golden
        config.save_outputs = save_outputs

        return self.run_config(config, confirm_update_golden=confirm_update_golden)

    def run_config(self, config: ScenarioConfig, confirm_update_golden: bool = False) -> ScenarioResult:
        run_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        self.logger.info(f"Starting scenario '{config.scenario_id}' (Run ID: {run_id})")

        result = ScenarioResult(
            run_id=run_id,
            scenario=config,
            status=ScenarioStatus.SKIPPED,
            started_at=started_at
        )

        sandbox_dir = self.build_sandbox_dir(run_id) if config.use_sandbox else Path(".")

        # Build Fixtures
        try:
             fixtures = []
             if config.symbols:
                  fixtures.append(self.fixture_builder.build_mock_symbol_universe(config.symbols))
             result.fixtures = fixtures
             self.fixture_builder.write_fixtures_to_sandbox(fixtures, sandbox_dir)
        except Exception as e:
             result.status = ScenarioStatus.ERROR
             result.issues.append(f"Failed to build fixtures: {str(e)}")
             return self._finalize_result(result)

        # Run steps
        overall_status = ScenarioStatus.SUCCESS
        for step in config.steps:
            self.logger.info(f"Executing step '{step.name}'")
            step_res = self.step_executor.execute_step(step, sandbox_dir)
            result.step_results.append(step_res)

            if step_res.status != ScenarioStatus.SUCCESS:
                if not step.continue_on_error and not config.continue_on_error:
                    overall_status = ScenarioStatus.FAILED
                    result.issues.append(f"Step '{step.name}' failed. Halting scenario.")
                    break
                else:
                    overall_status = ScenarioStatus.PARTIAL_SUCCESS
                    result.warnings.append(f"Step '{step.name}' failed but continue_on_error is true.")

        result.status = overall_status
        result.finished_at = datetime.utcnow()
        result.elapsed_seconds = (result.finished_at - result.started_at).total_seconds()

        # Validation
        validation_issues = self.validator.validate_result(result)
        if validation_issues:
             result.status = ScenarioStatus.FAILED
             result.issues.extend(validation_issues)

        # Golden Compare / Update
        if config.compare_golden and result.status in [ScenarioStatus.SUCCESS, ScenarioStatus.PARTIAL_SUCCESS]:
             comp = self.golden_manager.compare_to_snapshot(result)
             result.golden_comparison = comp.model_dump(mode='json')

        if config.update_golden and result.status in [ScenarioStatus.SUCCESS, ScenarioStatus.PARTIAL_SUCCESS]:
             try:
                 self.golden_manager.save_snapshot(result, confirm=confirm_update_golden)
                 self.logger.info("Golden snapshot updated successfully.")
             except Exception as e:
                 result.issues.append(f"Failed to update golden snapshot: {str(e)}")

        # Save
        if config.save_outputs:
            try:
                self.storage.save_result(result)
            except Exception as e:
                 result.warnings.append(f"Failed to save outputs: {str(e)}")

        self._audit_run(result)
        return result

    def _finalize_result(self, result: ScenarioResult) -> ScenarioResult:
         result.finished_at = datetime.utcnow()
         result.elapsed_seconds = (result.finished_at - result.started_at).total_seconds()
         return result

    def run_all(self, scenario_type: Optional[ScenarioType] = None, stop_on_failure: bool = False) -> List[ScenarioResult]:
        results = []
        for config in self.registry.list_scenarios():
            if scenario_type and config.scenario_type != scenario_type:
                 continue
            res = self.run_config(config)
            results.append(res)
            if stop_on_failure and res.status not in [ScenarioStatus.SUCCESS, ScenarioStatus.PARTIAL_SUCCESS]:
                break
        return results

    def replay(self, run_id: str) -> ScenarioResult:
        old_res = self.storage.load_result(run_id)
        if not old_res:
            raise ValueError(f"Run {run_id} not found.")
        return self.run_config(old_res.scenario)

    def build_sandbox_dir(self, run_id: str) -> Path:
        p = self.storage.get_scenario_runs_dir() / "sandbox" / run_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    def cleanup_sandbox(self, run_id: str, confirm: bool = False) -> Dict[str, Any]:
        if not confirm:
            raise ValueError("Cleanup requires explicit confirmation.")
        p = self.storage.get_scenario_runs_dir() / "sandbox" / run_id
        if p.exists():
             shutil.rmtree(p)
             return {"status": "success", "path": str(p)}
        return {"status": "not_found", "path": str(p)}

    def _audit_run(self, result: ScenarioResult):
         # Mock audit integration
         pass
