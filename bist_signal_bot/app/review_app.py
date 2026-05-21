from pathlib import Path
from typing import Optional

from ..config.settings import Settings
from ..review.storage import ReviewStore
from ..review.inbox import ReviewInboxManager
from ..review.decision import ReviewDecisionManager
from ..review.thesis import ReviewThesisBuilder
from ..review.checklist import ReviewChecklistBuilder
from ..review.followup import ReviewFollowupManager
from ..review.journal import DecisionJournal
from ..review.evidence import ReviewEvidenceCollector

def get_review_dir(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> Path:
    if base_dir:
        return base_dir / "review"
    if settings:
        data_dir = getattr(settings, "DATA_DIR", Path("data"))
        return Path(data_dir) / getattr(settings, "REVIEW_DIR_NAME", "review")
    return Path("data/review")

def create_review_store(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ReviewStore:
    path = get_review_dir(settings, base_dir)
    return ReviewStore(base_dir=path)

def create_review_inbox_manager(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ReviewInboxManager:
    store = create_review_store(settings, base_dir)
    ev_col = ReviewEvidenceCollector(settings)
    ch_build = ReviewChecklistBuilder(settings)
    return ReviewInboxManager(store=store, evidence_collector=ev_col, checklist_builder=ch_build, settings=settings)

def create_review_decision_manager(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ReviewDecisionManager:
    store = create_review_store(settings, base_dir)
    return ReviewDecisionManager(store=store, settings=settings)

def create_review_thesis_builder(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ReviewThesisBuilder:
    return ReviewThesisBuilder(settings=settings)

def create_review_checklist_builder(settings: Optional[Settings] = None) -> ReviewChecklistBuilder:
    return ReviewChecklistBuilder(settings=settings)

def create_review_followup_manager(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> ReviewFollowupManager:
    store = create_review_store(settings, base_dir)
    return ReviewFollowupManager(store=store, settings=settings)

def create_decision_journal(settings: Optional[Settings] = None, base_dir: Optional[Path] = None) -> DecisionJournal:
    store = create_review_store(settings, base_dir)
    return DecisionJournal(store=store, settings=settings)
