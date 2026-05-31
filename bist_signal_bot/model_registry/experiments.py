import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import ModelExperimentError
from bist_signal_bot.model_registry.models import ExperimentRun, ExperimentStatus, ModelKind


class ExperimentTracker:
    def __init__(self, settings: Settings | None = None, store: Any = None):
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)
        self.store = store

    def validate_run(self, run: ExperimentRun) -> list[str]:
        issues = []
        if not run.experiment_name:
            issues.append("experiment_name cannot be empty")
        if not run.model_name:
            issues.append("model_name cannot be empty")
        return issues

    def start_run(self, experiment_name: str, model_name: str, model_kind: ModelKind,
                  parameters: dict[str, Any] | None = None, feature_set_id: str | None = None) -> ExperimentRun:
        run_id = f"exp_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"

        run = ExperimentRun(
            run_id=run_id,
            experiment_name=experiment_name,
            model_name=model_name,
            model_kind=model_kind,
            status=ExperimentStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            parameters=parameters or {},
            feature_set_id=feature_set_id
        )

        issues = self.validate_run(run)
        if issues:
            self.logger.warning(f"Validation issues for started experiment run {run_id}: {issues}")

        if self.store:
            self.store.append_experiment_run(run)

        return run

    def complete_run(self, run_id: str, metrics: dict[str, float], warnings: list[str] | None = None) -> ExperimentRun:
        if not self.store:
            raise ModelExperimentError("Model store not configured")

        # Normally we would load the run by ID. If we don't have a get_run method,
        # we can load all and filter, or just assume the store handles updates.
        # Since our store is JSONL append-only, we append a new state.
        runs = self.store.load_experiment_runs()
        run = next((r for r in runs if r.run_id == run_id), None)

        if not run:
            raise ModelExperimentError(f"Experiment run not found: {run_id}")

        run.status = ExperimentStatus.COMPLETED
        run.metrics = metrics
        run.finished_at = datetime.now(timezone.utc)
        if warnings:
            run.warnings.extend(warnings)

        self.store.append_experiment_run(run)
        return run

    def fail_run(self, run_id: str, error_message: str) -> ExperimentRun:
        if not self.store:
            raise ModelExperimentError("Model store not configured")

        runs = self.store.load_experiment_runs()
        run = next((r for r in runs if r.run_id == run_id), None)

        if not run:
            raise ModelExperimentError(f"Experiment run not found: {run_id}")

        run.status = ExperimentStatus.FAILED
        run.finished_at = datetime.now(timezone.utc)
        run.warnings.append(f"Failed: {error_message}")

        self.store.append_experiment_run(run)
        return run

    def list_runs(self, experiment_name: str | None = None, limit: int = 1000) -> list[ExperimentRun]:
        if not self.store:
            return []
        return self.store.load_experiment_runs(experiment_name=experiment_name, limit=limit)

    def best_run(self, experiment_name: str, metric_name: str, maximize: bool = True) -> ExperimentRun | None:
        runs = self.list_runs(experiment_name=experiment_name)
        valid_runs = [r for r in runs if r.status == ExperimentStatus.COMPLETED and metric_name in r.metrics]

        if not valid_runs:
            return None

        valid_runs.sort(key=lambda r: r.metrics[metric_name], reverse=maximize)
        return valid_runs[0]
