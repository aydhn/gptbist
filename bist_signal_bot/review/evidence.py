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
