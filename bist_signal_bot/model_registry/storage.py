import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.core.exceptions import ModelRegistryStorageError
from bist_signal_bot.model_registry.models import (
    ModelRecord, ExperimentRun, ModelArtifact, ModelCard,
    ModelValidationSummary, ModelCalibrationSummary, ModelPromotionRequest,
    ModelDriftFinding, ModelLineageEdge, ModelGovernanceAssessment, ModelRegistryReport,
    ModelRegistryStatus
)
from bist_signal_bot.storage.paths import get_model_registry_dir


class ModelRegistryStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings or Settings()
        self.logger = logging.getLogger(__name__)
        self.base_dir = base_dir or get_model_registry_dir(self.settings)

    def _get_file(self, subdir: str, filename: str) -> Path:
        d = self.base_dir / subdir
        d.mkdir(parents=True, exist_ok=True)
        return d / filename

    def _append_jsonl(self, path: Path, obj: Any) -> Path:
        try:
            with open(path, "a", encoding="utf-8") as f:
                # Assuming obj is a Pydantic model with .model_dump_json() or .json() depending on version
                # In Pydantic v2 we use model_dump_json(), in v1 json()
                if hasattr(obj, "model_dump_json"):
                    f.write(obj.model_dump_json() + "\n")
                else:
                    f.write(obj.json() + "\n")
            return path
        except Exception as e:
            raise ModelRegistryStorageError(f"Failed to append to {path}: {e}")

    def _load_jsonl(self, path: Path, model_cls: Any) -> list[Any]:
        if not path.exists():
            return []
        results = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    # Pydantic v2 model_validate_json
                    if hasattr(model_cls, "model_validate_json"):
                        results.append(model_cls.model_validate_json(line))
                    else:
                        results.append(model_cls.parse_raw(line))
            return results
        except Exception as e:
            self.logger.warning(f"Error loading {path}: {e}")
            return []

    def append_model(self, model: ModelRecord) -> Path:
        return self._append_jsonl(self._get_file("models", "model_records.jsonl"), model)

    def load_models(self, status: ModelRegistryStatus | None = None, limit: int = 10000) -> list[ModelRecord]:
        models = self._load_jsonl(self._get_file("models", "model_records.jsonl"), ModelRecord)
        # Handle updates (last write wins)
        latest_models = {}
        for m in models:
            latest_models[m.model_id] = m

        result = list(latest_models.values())
        if status:
            result = [m for m in result if m.status == status]

        # Sort by updated_at or created_at descending
        result.sort(key=lambda m: m.updated_at or m.created_at, reverse=True)
        return result[:limit]

    def get_model(self, model_id_or_name: str) -> ModelRecord | None:
        models = self.load_models()
        for m in models:
            if m.model_id == model_id_or_name or m.model_name == model_id_or_name:
                return m
        return None

    def append_experiment_run(self, run: ExperimentRun) -> Path:
        return self._append_jsonl(self._get_file("experiments", "experiment_runs.jsonl"), run)

    def load_experiment_runs(self, experiment_name: str | None = None, limit: int = 10000) -> list[ExperimentRun]:
        runs = self._load_jsonl(self._get_file("experiments", "experiment_runs.jsonl"), ExperimentRun)

        # Keep latest state per run_id
        latest_runs = {}
        for r in runs:
            latest_runs[r.run_id] = r

        result = list(latest_runs.values())
        if experiment_name:
            result = [r for r in result if r.experiment_name == experiment_name]

        result.sort(key=lambda r: r.started_at, reverse=True)
        return result[:limit]

    def append_artifact(self, artifact: ModelArtifact) -> Path:
        return self._append_jsonl(self._get_file("artifacts", "model_artifacts.jsonl"), artifact)

    def load_artifacts(self, model_id: str | None = None, limit: int = 10000) -> list[ModelArtifact]:
        artifacts = self._load_jsonl(self._get_file("artifacts", "model_artifacts.jsonl"), ModelArtifact)
        if model_id:
            artifacts = [a for a in artifacts if a.model_id == model_id]
        artifacts.sort(key=lambda a: a.created_at, reverse=True)
        return artifacts[:limit]

    def append_model_card(self, card: ModelCard) -> Path:
        return self._append_jsonl(self._get_file("cards", "model_cards.jsonl"), card)

    def load_model_cards(self, model_id: str | None = None, limit: int = 10000) -> list[ModelCard]:
        cards = self._load_jsonl(self._get_file("cards", "model_cards.jsonl"), ModelCard)
        if model_id:
            cards = [c for c in cards if c.model_id == model_id]
        cards.sort(key=lambda c: c.created_at, reverse=True)
        return cards[:limit]

    def append_validation_summary(self, summary: ModelValidationSummary) -> Path:
        return self._append_jsonl(self._get_file("validation", "model_validation_summaries.jsonl"), summary)

    def load_validation_summaries(self, model_id: str | None = None, limit: int = 10000) -> list[ModelValidationSummary]:
        summaries = self._load_jsonl(self._get_file("validation", "model_validation_summaries.jsonl"), ModelValidationSummary)
        if model_id:
            summaries = [s for s in summaries if s.model_id == model_id]
        summaries.sort(key=lambda s: s.created_at, reverse=True)
        return summaries[:limit]

    def append_calibration_summary(self, summary: ModelCalibrationSummary) -> Path:
        return self._append_jsonl(self._get_file("calibration", "model_calibration_summaries.jsonl"), summary)

    def load_calibration_summaries(self, model_id: str | None = None, limit: int = 10000) -> list[ModelCalibrationSummary]:
        summaries = self._load_jsonl(self._get_file("calibration", "model_calibration_summaries.jsonl"), ModelCalibrationSummary)
        if model_id:
            summaries = [s for s in summaries if s.model_id == model_id]
        summaries.sort(key=lambda s: s.created_at, reverse=True)
        return summaries[:limit]

    def append_promotion_request(self, request: ModelPromotionRequest) -> Path:
        return self._append_jsonl(self._get_file("promotion", "model_promotion_requests.jsonl"), request)

    def load_promotion_requests(self, model_id: str | None = None, limit: int = 10000) -> list[ModelPromotionRequest]:
        reqs = self._load_jsonl(self._get_file("promotion", "model_promotion_requests.jsonl"), ModelPromotionRequest)

        # Handle state updates (approved/rejected)
        latest_reqs = {}
        for r in reqs:
            latest_reqs[r.promotion_id] = r

        result = list(latest_reqs.values())
        if model_id:
            result = [r for r in result if r.model_id == model_id]

        result.sort(key=lambda r: r.requested_at, reverse=True)
        return result[:limit]

    def append_drift_findings(self, findings: list[ModelDriftFinding]) -> Path:
        path = self._get_file("drift", "model_drift_findings.jsonl")
        for f in findings:
            self._append_jsonl(path, f)
        return path

    def load_drift_findings(self, model_id: str | None = None, limit: int = 10000) -> list[ModelDriftFinding]:
        findings = self._load_jsonl(self._get_file("drift", "model_drift_findings.jsonl"), ModelDriftFinding)
        if model_id:
            findings = [f for f in findings if f.model_id == model_id]
        # Sort by drift_id/timestamp loosely based on format
        findings.reverse() # rough reverse chronological if appended sequentially
        return findings[:limit]

    def append_lineage_edges(self, edges: list[ModelLineageEdge]) -> Path:
        path = self._get_file("lineage", "model_lineage_edges.jsonl")
        for e in edges:
            self._append_jsonl(path, e)
        return path

    def load_lineage_edges(self) -> list[ModelLineageEdge]:
        return self._load_jsonl(self._get_file("lineage", "model_lineage_edges.jsonl"), ModelLineageEdge)

    def append_governance_assessment(self, assessment: ModelGovernanceAssessment) -> Path:
        return self._append_jsonl(self._get_file("governance", "model_governance_assessments.jsonl"), assessment)

    def load_latest_governance(self, model_id: str) -> ModelGovernanceAssessment | None:
        assessments = self._load_jsonl(self._get_file("governance", "model_governance_assessments.jsonl"), ModelGovernanceAssessment)
        model_assessments = [a for a in assessments if a.model_id == model_id]
        if not model_assessments:
            return None
        model_assessments.sort(key=lambda a: a.created_at, reverse=True)
        return model_assessments[0]

    def save_report(self, report: ModelRegistryReport, markdown_text: str) -> dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        report_dir = self._get_file("reports", date_str)
        report_dir.mkdir(parents=True, exist_ok=True)

        json_path = report_dir / f"model_registry_report_{report.report_id}.json"
        md_path = report_dir / f"model_registry_report_{report.report_id}.md"

        try:
            with open(json_path, "w", encoding="utf-8") as f:
                if hasattr(report, "model_dump_json"):
                    f.write(report.model_dump_json(indent=2))
                else:
                    f.write(report.json(indent=2))

            with open(md_path, "w", encoding="utf-8") as f:
                f.write(markdown_text)

            return {"json": json_path, "markdown": md_path}
        except Exception as e:
            raise ModelRegistryStorageError(f"Failed to save report: {e}")
