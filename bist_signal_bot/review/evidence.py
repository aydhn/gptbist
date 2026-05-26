from typing import Any
import uuid
from typing import List

from .models import ReviewEvidence, ReviewEvidenceType, ReviewItem

class ReviewEvidenceCollector:

    def get_similar_cases(self, item_id: str, settings: Any = None) -> list:
        try:
            from bist_signal_bot.app.knowledge_app import create_evidence_retriever
            retriever = create_evidence_retriever(settings)
            return retriever.retrieve_for_review_item(item_id)
        except Exception:
            return []
    def __init__(self, settings=None):
        self.settings = settings

    def collect_for_item(self, item: ReviewItem) -> List[ReviewEvidence]:
        evidence = []
        evidence.extend(self.collect_signal_evidence(item))
        evidence.extend(self.collect_risk_evidence(item))
        evidence.extend(self.collect_fundamental_evidence(item))
        evidence.extend(self.collect_breadth_evidence(item))
        evidence.extend(self.collect_stress_drift_evidence(item))
        return evidence

    def _create_empty_evidence(self, item: ReviewItem, ev_type: ReviewEvidenceType, title: str) -> ReviewEvidence:
        return ReviewEvidence(
            evidence_id=str(uuid.uuid4()),
            item_id=item.item_id,
            evidence_type=ev_type,
            title=title,
            summary="No evidence available.",
            warnings=["Source data not found"]
        )

    def collect_signal_evidence(self, item: ReviewItem) -> List[ReviewEvidence]:
        return [self._create_empty_evidence(item, ReviewEvidenceType.TECHNICAL, "Technical Signal")]

    def collect_ensemble_evidence(self, item: ReviewItem) -> List[ReviewEvidence]:
        return [self._create_empty_evidence(item, ReviewEvidenceType.ENSEMBLE, "Ensemble Consensus")]

    def collect_risk_evidence(self, item: ReviewItem) -> List[ReviewEvidence]:
        return [self._create_empty_evidence(item, ReviewEvidenceType.RISK, "Risk Status")]

    def collect_fundamental_evidence(self, item: ReviewItem) -> List[ReviewEvidence]:
        return [self._create_empty_evidence(item, ReviewEvidenceType.FUNDAMENTAL, "Fundamental Context")]

    def collect_breadth_evidence(self, item: ReviewItem) -> List[ReviewEvidence]:
        return [self._create_empty_evidence(item, ReviewEvidenceType.BREADTH, "Breadth Context")]

    def collect_stress_drift_evidence(self, item: ReviewItem) -> List[ReviewEvidence]:
        return [self._create_empty_evidence(item, ReviewEvidenceType.STRESS, "Stress/Drift Status")]

    def collect_history_evidence(self, item: ReviewItem) -> List[ReviewEvidence]:
        return []

    def attach_validation_summary(self, validation_result) -> None:
        pass

    def collect_whatif_evidence(self, item: ReviewItem, whatif_run_result: Any) -> List[ReviewEvidence]:
        if not whatif_run_result:
            return []

        summary = ""
        warnings = []
        if hasattr(whatif_run_result, "comparison") and whatif_run_result.comparison:
            summary = f"What-If Comparison: {len(whatif_run_result.comparison.scenario_results)} scenarios."
            if whatif_run_result.comparison.best_scenario_id:
                summary += f" Best: {whatif_run_result.comparison.best_scenario_id}."
            warnings = whatif_run_result.comparison.key_findings

        return [ReviewEvidence(
            evidence_id=str(uuid.uuid4()),
            item_id=item.item_id,
            evidence_type=ReviewEvidenceType.CUSTOM,
            title="What-If Scenario Summary",
            summary=summary,
            warnings=warnings,
            metadata={"source": "whatif_lab", "whatif_summary": whatif_run_result.summary() if hasattr(whatif_run_result, 'summary') else {}}
        )]
