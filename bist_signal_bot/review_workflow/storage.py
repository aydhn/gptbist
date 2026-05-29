import json
import logging
from pathlib import Path
from typing import Any, List, Optional, Dict
from datetime import datetime
from bist_signal_bot.review_workflow.models import (
    ReviewCase, ReviewPlaybook, ReviewChecklistItem, DecisionJournalEntry,
    ReviewSignoffRequest, ReviewDataAction, ReviewPattern, ReviewWorkflowReport,
    ReviewCaseStatus, ReviewCaseType, ReviewCasePriority, ReviewDisposition, SignoffStatus, ChecklistItemStatus, ReviewPlaybookType
)

logger = logging.getLogger(__name__)

class ReviewWorkflowStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.cases_dir = base_dir / "cases"
        self.playbooks_dir = base_dir / "playbooks"
        self.checklists_dir = base_dir / "checklists"
        self.journal_dir = base_dir / "journal"
        self.signoffs_dir = base_dir / "signoffs"
        self.data_actions_dir = base_dir / "data_actions"
        self.patterns_dir = base_dir / "patterns"
        self.reports_dir = base_dir / "reports"

        for d in [self.cases_dir, self.playbooks_dir, self.checklists_dir,
                  self.journal_dir, self.signoffs_dir, self.data_actions_dir,
                  self.patterns_dir, self.reports_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _serialize_datetime(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, (ReviewCaseStatus, ReviewCaseType, ReviewCasePriority,
                            ReviewDisposition, SignoffStatus, ChecklistItemStatus, ReviewPlaybookType)):
            return obj.name
        raise TypeError(f"Type {type(obj)} not serializable")

    def _append_jsonl(self, path: Path, data: dict):
        with open(path, "a") as f:
            f.write(json.dumps(data, default=self._serialize_datetime) + "\n")

    def append_case(self, case: ReviewCase) -> Path:
        path = self.cases_dir / "review_cases.jsonl"
        self._append_jsonl(path, case.__dict__)
        return path

    def load_cases(self, status: Optional[ReviewCaseStatus] = None, symbol: Optional[str] = None, limit: int = 1000) -> List[ReviewCase]:
        path = self.cases_dir / "review_cases.jsonl"
        if not path.exists():
            return []

        # We need to construct actual objects
        cases = []
        with open(path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    # Simplified parsing for testing
                    if 'created_at' in data:
                        data['created_at'] = datetime.fromisoformat(data['created_at'])
                    if 'updated_at' in data:
                        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
                    if 'closed_at' in data and data['closed_at']:
                        data['closed_at'] = datetime.fromisoformat(data['closed_at'])

                    data['status'] = ReviewCaseStatus[data['status']]
                    data['case_type'] = ReviewCaseType[data['case_type']]
                    data['priority'] = ReviewCasePriority[data['priority']]
                    data['disposition'] = ReviewDisposition[data['disposition']]
                    data['signoff_status'] = SignoffStatus[data['signoff_status']]

                    case = ReviewCase(**data)

                    if status and case.status != status:
                        continue
                    if symbol and case.symbol != symbol:
                        continue

                    cases.append(case)
                except Exception as e:
                    logger.warning(f"Error parsing case line: {e}")

        # Since append-only, return the latest version of each case
        case_map = {c.case_id: c for c in cases}
        result = list(case_map.values())
        return result[-limit:] if limit else result

    def get_case(self, case_id: str) -> Optional[ReviewCase]:
        cases = self.load_cases()
        for case in cases:
            if case.case_id == case_id:
                return case
        return None

    def update_case_append_version(self, case: ReviewCase) -> Path:
        return self.append_case(case)

    def save_playbooks(self, playbooks: List[ReviewPlaybook]) -> Path:
        path = self.playbooks_dir / "review_playbooks.json"
        with open(path, "w") as f:
            json.dump([pb.__dict__ for pb in playbooks], f, default=self._serialize_datetime, indent=2)
        return path

    def load_playbooks(self) -> List[ReviewPlaybook]:
        path = self.playbooks_dir / "review_playbooks.json"
        if not path.exists():
            return []

        with open(path, "r") as f:
            data_list = json.load(f)

        playbooks = []
        for data in data_list:
            try:
                data['playbook_type'] = ReviewPlaybookType[data['playbook_type']]
                if data.get('required_signoff_priority'):
                    data['required_signoff_priority'] = ReviewCasePriority[data['required_signoff_priority']]
                playbooks.append(ReviewPlaybook(**data))
            except Exception as e:
                logger.warning(f"Error parsing playbook: {e}")
        return playbooks

    def append_journal_entry(self, entry: DecisionJournalEntry) -> Path:
        path = self.journal_dir / "decision_journal.jsonl"
        self._append_jsonl(path, entry.__dict__)
        return path

    def load_journal(self, case_id: Optional[str] = None, limit: int = 1000) -> List[DecisionJournalEntry]:
        path = self.journal_dir / "decision_journal.jsonl"
        if not path.exists():
            return []

        entries = []
        with open(path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if case_id and data.get("case_id") != case_id:
                        continue

                    if 'created_at' in data:
                        data['created_at'] = datetime.fromisoformat(data['created_at'])
                    if data.get('previous_status'):
                        data['previous_status'] = ReviewCaseStatus[data['previous_status']]
                    if data.get('new_status'):
                        data['new_status'] = ReviewCaseStatus[data['new_status']]
                    if data.get('disposition'):
                        data['disposition'] = ReviewDisposition[data['disposition']]

                    entries.append(DecisionJournalEntry(**data))
                except Exception as e:
                    logger.warning(f"Error parsing journal line: {e}")

        return entries[-limit:] if limit else entries

    def append_signoff(self, signoff: ReviewSignoffRequest) -> Path:
        path = self.signoffs_dir / "review_signoffs.jsonl"
        self._append_jsonl(path, signoff.__dict__)
        return path

    def load_signoffs(self, case_id: Optional[str] = None, limit: int = 1000) -> List[ReviewSignoffRequest]:
        path = self.signoffs_dir / "review_signoffs.jsonl"
        if not path.exists():
            return []

        signoffs = []
        with open(path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if case_id and data.get("case_id") != case_id:
                        continue

                    if 'requested_at' in data:
                        data['requested_at'] = datetime.fromisoformat(data['requested_at'])
                    if 'approved_at' in data and data['approved_at']:
                        data['approved_at'] = datetime.fromisoformat(data['approved_at'])
                    if 'expires_at' in data and data['expires_at']:
                        data['expires_at'] = datetime.fromisoformat(data['expires_at'])

                    data['status'] = SignoffStatus[data['status']]
                    signoffs.append(ReviewSignoffRequest(**data))
                except Exception as e:
                    logger.warning(f"Error parsing signoff line: {e}")

        # Return latest version of each signoff
        so_map = {s.signoff_id: s for s in signoffs}
        result = list(so_map.values())
        return result[-limit:] if limit else result

    def append_data_actions(self, actions: List[ReviewDataAction]) -> Path:
        path = self.data_actions_dir / "review_data_actions.jsonl"
        for act in actions:
            self._append_jsonl(path, act.__dict__)
        return path

    def load_data_actions(self, status: Optional[str] = None, limit: int = 1000) -> List[ReviewDataAction]:
        path = self.data_actions_dir / "review_data_actions.jsonl"
        if not path.exists():
            return []

        actions = []
        with open(path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if 'created_at' in data:
                        data['created_at'] = datetime.fromisoformat(data['created_at'])
                    if 'resolved_at' in data and data['resolved_at']:
                        data['resolved_at'] = datetime.fromisoformat(data['resolved_at'])
                    if 'priority' in data:
                        data['priority'] = ReviewCasePriority[data['priority']]

                    action = ReviewDataAction(**data)
                    if status and action.status != status:
                        continue
                    actions.append(action)
                except Exception as e:
                    logger.warning(f"Error parsing action line: {e}")

        act_map = {a.action_id: a for a in actions}
        result = list(act_map.values())
        return result[-limit:] if limit else result

    def append_patterns(self, patterns: List[ReviewPattern]) -> Path:
        path = self.patterns_dir / "review_patterns.jsonl"
        for pat in patterns:
            self._append_jsonl(path, pat.__dict__)
        return path

    def save_report(self, report: ReviewWorkflowReport, markdown_text: str) -> Dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        report_dir = self.reports_dir / date_str
        report_dir.mkdir(parents=True, exist_ok=True)

        json_path = report_dir / "review_workflow_report.json"
        with open(json_path, "w") as f:
            # Need to convert models to dict before dump
            d = report.__dict__.copy()
            d['cases'] = []
            d['journal_entries'] = []
            d['signoffs'] = []
            d['data_actions'] = []
            d['patterns'] = []
            json.dump(d, f, default=self._serialize_datetime, indent=2)

        md_path = report_dir / "review_workflow_report.md"
        with open(md_path, "w") as f:
            f.write(markdown_text)

        return {"json": json_path, "markdown": md_path}

    def append_checklist_items(self, items: List[ReviewChecklistItem]) -> Path:
        path = self.checklists_dir / "review_checklists.jsonl"
        for item in items:
            self._append_jsonl(path, item.__dict__)
        return path

    def load_checklist(self, case_id: str) -> List[ReviewChecklistItem]:
        path = self.checklists_dir / "review_checklists.jsonl"
        if not path.exists():
            return []

        items = []
        with open(path, "r") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get("case_id") != case_id:
                        continue
                    data['status'] = ChecklistItemStatus[data['status']]
                    items.append(ReviewChecklistItem(**data))
                except Exception as e:
                    logger.warning(f"Error parsing checklist line: {e}")

        # Return latest versions
        item_map = {i.item_id: i for i in items}
        return list(item_map.values())
