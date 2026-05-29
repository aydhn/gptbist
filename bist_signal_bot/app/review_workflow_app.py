from pathlib import Path
from typing import Optional, Any

from bist_signal_bot.review_workflow.storage import ReviewWorkflowStore
from bist_signal_bot.review_workflow.playbooks import ReviewPlaybookRegistry
from bist_signal_bot.review_workflow.priority import ReviewPriorityEngine
from bist_signal_bot.review_workflow.case_builder import ReviewCaseBuilder
from bist_signal_bot.review_workflow.checklist import ReviewChecklistBuilder
from bist_signal_bot.review_workflow.journal import DecisionJournal
from bist_signal_bot.review_workflow.signoff import ReviewSignoffManager
from bist_signal_bot.review_workflow.data_actions import ReviewDataActionQueue
from bist_signal_bot.review_workflow.patterns import ReviewPatternDetector

# Mock Settings for type hinting without circular dependency
class DummySettings:
    DATA_DIR = Path("data")

def create_review_workflow_store(settings: Any = None, base_dir: Optional[Path] = None) -> ReviewWorkflowStore:
    if not base_dir:
        base_dir = Path("data/review_workflow") if not settings else getattr(settings, "DATA_DIR", Path("data")) / "review_workflow"
    return ReviewWorkflowStore(base_dir=base_dir)

def create_review_playbook_registry(settings: Any = None, base_dir: Optional[Path] = None) -> ReviewPlaybookRegistry:
    return ReviewPlaybookRegistry()

def create_review_priority_engine(settings: Any = None) -> ReviewPriorityEngine:
    return ReviewPriorityEngine()

def create_review_case_builder(settings: Any = None, base_dir: Optional[Path] = None) -> ReviewCaseBuilder:
    registry = create_review_playbook_registry(settings, base_dir)
    priority = create_review_priority_engine(settings)
    return ReviewCaseBuilder(playbook_registry=registry, priority_engine=priority)

def create_review_checklist_builder(settings: Any = None) -> ReviewChecklistBuilder:
    return ReviewChecklistBuilder()

def create_decision_journal(settings: Any = None, base_dir: Optional[Path] = None) -> DecisionJournal:
    store = create_review_workflow_store(settings, base_dir)
    return DecisionJournal(store=store)

def create_review_signoff_manager(settings: Any = None, base_dir: Optional[Path] = None) -> ReviewSignoffManager:
    store = create_review_workflow_store(settings, base_dir)
    return ReviewSignoffManager(store=store)

def create_review_data_action_queue(settings: Any = None, base_dir: Optional[Path] = None) -> ReviewDataActionQueue:
    store = create_review_workflow_store(settings, base_dir)
    return ReviewDataActionQueue(store=store)

def create_review_pattern_detector(settings: Any = None) -> ReviewPatternDetector:
    min_count = 3
    if settings:
        min_count = getattr(settings, "REVIEW_PATTERN_MIN_COUNT", 3)
    return ReviewPatternDetector(min_count=min_count)
