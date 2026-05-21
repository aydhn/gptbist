from datetime import datetime, timezone
import uuid
from typing import List

from .models import (
    ReviewItem, ReviewChecklist, ReviewChecklistItem, ChecklistItemStatus, ReviewEvidence
)

class ReviewChecklistBuilder:
    def __init__(self, settings=None):
        self.settings = settings

    def build_default_checklist(self, item: ReviewItem, evidence: List[ReviewEvidence]) -> ReviewChecklist:
        items = [
            ReviewChecklistItem(item_id=item.item_id, name="data_quality_checked", required=True),
            ReviewChecklistItem(item_id=item.item_id, name="signal_not_duplicate", required=True),
            ReviewChecklistItem(item_id=item.item_id, name="risk_engine_pass_or_warn", required=True),
            ReviewChecklistItem(item_id=item.item_id, name="regime_context_reviewed", required=False),
            ReviewChecklistItem(item_id=item.item_id, name="breadth_context_reviewed", required=False),
            ReviewChecklistItem(item_id=item.item_id, name="fundamental_context_reviewed", required=False),
            ReviewChecklistItem(item_id=item.item_id, name="ensemble_conflicts_reviewed", required=False),
            ReviewChecklistItem(item_id=item.item_id, name="stress_context_reviewed", required=False),
            ReviewChecklistItem(item_id=item.item_id, name="drift_context_reviewed", required=False),
            ReviewChecklistItem(item_id=item.item_id, name="governance_text_safe", required=True),
            ReviewChecklistItem(item_id=item.item_id, name="no_real_order_language", required=True),
            ReviewChecklistItem(item_id=item.item_id, name="thesis_written", required=True),
        ]
        now = datetime.now(timezone.utc)
        checklist = ReviewChecklist(
            checklist_id=str(uuid.uuid4()),
            item_id=item.item_id,
            created_at=now,
            updated_at=now,
            items=items
        )
        return checklist

    def evaluate_checklist(self, item: ReviewItem, checklist: ReviewChecklist, evidence: List[ReviewEvidence]) -> ReviewChecklist:
        checklist.pass_count = 0
        checklist.warn_count = 0
        checklist.fail_count = 0
        checklist.required_fail_count = 0

        for c_item in checklist.items:
            if c_item.status == ChecklistItemStatus.PASS:
                checklist.pass_count += 1
            elif c_item.status == ChecklistItemStatus.WARN:
                checklist.warn_count += 1
            elif c_item.status == ChecklistItemStatus.FAIL:
                checklist.fail_count += 1
                if c_item.required:
                    checklist.required_fail_count += 1

        checklist.overall_status = self.overall_status(checklist.items)
        checklist.updated_at = datetime.now(timezone.utc)
        return checklist

    def update_checklist_item(self, checklist_id: str, item_name: str, status: ChecklistItemStatus, message: str) -> ReviewChecklist:
        # Bu metod store/repo entegrasyonu olmadan havada çalışmaz,
        # Genelde bir 'store' gerekir ama istenilen signature buydu,
        # geçici olarak None döneceğiz veya checklist argümanını ekleyeceğiz.
        # Impl için checklist state'i bir şekilde almak gerekir,
        # Bunu inbox veya storage yönetecek.
        pass

    def overall_status(self, items: List[ReviewChecklistItem]) -> ChecklistItemStatus:
        fails = 0
        required_fails = 0
        warns = 0
        passes = 0
        unknowns = 0

        for item in items:
            if item.status == ChecklistItemStatus.FAIL:
                fails += 1
                if item.required:
                    required_fails += 1
            elif item.status == ChecklistItemStatus.WARN:
                warns += 1
            elif item.status == ChecklistItemStatus.PASS:
                passes += 1
            else:
                unknowns += 1

        if required_fails > 0:
            return ChecklistItemStatus.FAIL
        if fails > 0:
            return ChecklistItemStatus.WARN # Required değilse warn yapabiliriz genel mantıkta, ama fail da olabilir.
        if warns > 0:
            return ChecklistItemStatus.WARN
        if unknowns > 0:
            return ChecklistItemStatus.UNKNOWN

        return ChecklistItemStatus.PASS
