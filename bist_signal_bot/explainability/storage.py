import json
from pathlib import Path
from typing import Any
from bist_signal_bot.explainability.models import (
    LocalExplanation,
    GlobalExplanation,
    SensitivityAnalysisResult,
    DecisionTrace,
    RuleTrace,
    CounterfactualScenario,
    ExplanationCohort,
    ExplanationGovernanceAssessment,
    ExplainabilityReport,
    SignalExplanation,
    EvidenceCard
)
from bist_signal_bot.storage.paths import get_explainability_dir

class ExplainabilityStore:
    def __init__(self, settings: Any = None, base_dir: Path | None = None):
        self.settings = settings
        if base_dir is None:
            self.base_dir = get_explainability_dir(settings)
        else:
            self.base_dir = base_dir
            self.base_dir.mkdir(parents=True, exist_ok=True)

        self.local_dir = self.base_dir / "local"
        self.global_dir = self.base_dir / "global"
        self.sensitivity_dir = self.base_dir / "sensitivity"
        self.decision_traces_dir = self.base_dir / "decision_traces"
        self.rule_traces_dir = self.base_dir / "rule_traces"
        self.counterfactuals_dir = self.base_dir / "counterfactuals"
        self.cohorts_dir = self.base_dir / "cohorts"
        self.governance_dir = self.base_dir / "governance"
        self.reports_dir = self.base_dir / "reports"
        self.signals_dir = self.base_dir / "signal_explanations"
        self.cards_dir = self.base_dir / "evidence_cards"

        for d in [self.local_dir, self.global_dir, self.sensitivity_dir, self.decision_traces_dir,
                  self.rule_traces_dir, self.counterfactuals_dir, self.cohorts_dir,
                  self.governance_dir, self.reports_dir, self.signals_dir, self.cards_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _append_jsonl(self, file_path: Path, model_obj: Any) -> Path:
        with open(file_path, "a") as f:
            f.write(model_obj.model_dump_json() + "\n")
        return file_path

    def _load_jsonl(self, file_path: Path, model_class: Any, object_id: str | None = None, limit: int = 1000) -> list[Any]:
        if not file_path.exists():
            return []
        res = []
        with open(file_path, "r") as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                if object_id and data.get("object_id") != object_id: continue
                res.append(model_class(**data))
        return res[-limit:]

    def append_local_explanation(self, explanation: LocalExplanation) -> Path:
        return self._append_jsonl(self.local_dir / "local_explanations.jsonl", explanation)

    def load_local_explanations(self, object_id: str | None = None, limit: int = 1000) -> list[LocalExplanation]:
        return self._load_jsonl(self.local_dir / "local_explanations.jsonl", LocalExplanation, object_id, limit)

    def append_global_explanation(self, explanation: GlobalExplanation) -> Path:
        return self._append_jsonl(self.global_dir / "global_explanations.jsonl", explanation)

    def load_global_explanations(self, object_id: str | None = None, limit: int = 1000) -> list[GlobalExplanation]:
        return self._load_jsonl(self.global_dir / "global_explanations.jsonl", GlobalExplanation, object_id, limit)

    def append_sensitivity_result(self, result: SensitivityAnalysisResult) -> Path:
        return self._append_jsonl(self.sensitivity_dir / "sensitivity_results.jsonl", result)

    def append_decision_trace(self, trace: DecisionTrace) -> Path:
        return self._append_jsonl(self.decision_traces_dir / "decision_traces.jsonl", trace)

    def append_rule_trace(self, trace: RuleTrace) -> Path:
        return self._append_jsonl(self.rule_traces_dir / "rule_traces.jsonl", trace)

    def append_counterfactuals(self, items: list[CounterfactualScenario]) -> Path:
        p = self.counterfactuals_dir / "counterfactuals.jsonl"
        for item in items:
            self._append_jsonl(p, item)
        return p

    def append_cohort(self, cohort: ExplanationCohort) -> Path:
        return self._append_jsonl(self.cohorts_dir / "explanation_cohorts.jsonl", cohort)

    def append_governance_assessment(self, assessment: ExplanationGovernanceAssessment) -> Path:
        return self._append_jsonl(self.governance_dir / "explanation_governance.jsonl", assessment)

    def load_latest_governance(self, object_id: str) -> ExplanationGovernanceAssessment | None:
        assessments = self._load_jsonl(self.governance_dir / "explanation_governance.jsonl", ExplanationGovernanceAssessment, object_id, limit=1)
        return assessments[0] if assessments else None

    def save_report(self, report: ExplainabilityReport, markdown_text: str) -> dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        daily_dir = self.reports_dir / date_str
        daily_dir.mkdir(parents=True, exist_ok=True)

        json_path = daily_dir / "explainability_report.json"
        md_path = daily_dir / "explainability_report.md"

        with open(json_path, "w") as f:
            f.write(report.model_dump_json(indent=2))
        with open(md_path, "w") as f:
            f.write(markdown_text)

        return {"json": json_path, "md": md_path}

    def load_decision_traces(self, symbol: str | None = None, limit: int = 1000) -> list[DecisionTrace]:
        p = self.decision_traces_dir / "decision_traces.jsonl"
        return self._load_jsonl(p, DecisionTrace, None, limit)

    def load_signal_explanations(self, symbol: str | None = None, limit: int = 1000) -> list[SignalExplanation]:
        return self._load_jsonl(self.signals_dir / "signal_explanations.jsonl", SignalExplanation, None, limit)

    def append_evidence_card(self, card: EvidenceCard) -> Path:
        return self._append_jsonl(self.cards_dir / "evidence_cards.jsonl", card)

    def append_signal_explanation(self, explanation: SignalExplanation) -> Path:
        return self._append_jsonl(self.signals_dir / "signal_explanations.jsonl", explanation)
