import uuid
from typing import Any, List, Optional
from bist_signal_bot.review_workflow.models import ReviewChecklistItem, ChecklistItemStatus, ReviewPlaybook, ReviewCase

class ReviewChecklistBuilder:
    def build_checklist(self, case_id: str, playbooks: List[ReviewPlaybook], snapshot: Any = None) -> List[ReviewChecklistItem]:
        items = []
        items.extend(self.standard_signal_items(case_id))

        for playbook in playbooks:
            if playbook.playbook_type.name != "STANDARD_SIGNAL_REVIEW":
                items.extend(self.items_for_playbook(case_id, playbook))

        # Deduplicate by title
        seen_titles = set()
        unique_items = []
        for item in items:
            if item.title not in seen_titles:
                seen_titles.add(item.title)
                unique_items.append(item)

        return unique_items

    def standard_signal_items(self, case_id: str) -> List[ReviewChecklistItem]:
        return [
            ReviewChecklistItem(
                item_id=str(uuid.uuid4()),
                case_id=case_id,
                title="Context Snapshot Up-to-date",
                description="Verify that the unified context snapshot is fresh and valid.",
                required=True
            ),
            ReviewChecklistItem(
                item_id=str(uuid.uuid4()),
                case_id=case_id,
                title="No Critical Conflicts",
                description="Check if there are any critical context conflicts.",
                required=True
            ),
            ReviewChecklistItem(
                item_id=str(uuid.uuid4()),
                case_id=case_id,
                title="No Evidence Gaps",
                description="Verify that all required data layers have evidence.",
                required=True
            ),
            ReviewChecklistItem(
                item_id=str(uuid.uuid4()),
                case_id=case_id,
                title="Safe Language Disclaimer",
                description="Verify that no investment advice or real trade instruction language is used.",
                required=True
            )
        ]

    def items_for_playbook(self, case_id: str, playbook: ReviewPlaybook) -> List[ReviewChecklistItem]:
        items = []
        if playbook.playbook_type.name == "MACRO_PRESSURE":
            items.append(ReviewChecklistItem(
                item_id=str(uuid.uuid4()),
                case_id=case_id,
                title="Macro Pressure Check",
                description="Evaluate the impact of macro pressure on this case."
            ))
        elif playbook.playbook_type.name == "EVENT_BLACKOUT":
            items.append(ReviewChecklistItem(
                item_id=str(uuid.uuid4()),
                case_id=case_id,
                title="Event Blackout Check",
                description="Evaluate the risk of trading during an event blackout."
            ))
        elif playbook.playbook_type.name == "MISSING_DATA":
            items.append(ReviewChecklistItem(
                item_id=str(uuid.uuid4()),
                case_id=case_id,
                title="Resolve Data Gaps",
                description="Resolve missing data before continuing review."
            ))
        else:
            items.append(ReviewChecklistItem(
                item_id=str(uuid.uuid4()),
                case_id=case_id,
                title=f"{playbook.name} Check",
                description=f"Evaluate based on {playbook.name} playbook."
            ))
        return items

    def evaluate_checklist(self, case: ReviewCase, evidence: dict[str, Any] = None) -> List[ReviewChecklistItem]:
        for item in case.checklist:
            if item.title == "Context Snapshot Up-to-date" and case.snapshot_id:
                item.status = ChecklistItemStatus.PASSED
            elif item.title == "No Critical Conflicts" and not any(c for c in case.conflicts if "CRITICAL" in c):
                item.status = ChecklistItemStatus.PASSED
            elif item.title == "No Evidence Gaps" and not case.evidence_gaps:
                item.status = ChecklistItemStatus.PASSED

        return case.checklist

    def completion_rate(self, items: List[ReviewChecklistItem]) -> Optional[float]:
        if not items:
            return None
        passed = sum(1 for item in items if item.status == ChecklistItemStatus.PASSED)
        return (passed / len(items)) * 100.0
