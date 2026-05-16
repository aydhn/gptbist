import uuid
import logging
from typing import Any

from ..config.settings import Settings, get_settings
from .models import AttributionReport, AttributionBucket, AttributionGroupBy, SignalJournalEntry, ResearchSignalOutcome
from .journal import SignalJournal
from ..core.exceptions import ResearchAttributionError

class ResearchAttributionEngine:
    def __init__(self, journal: SignalJournal, settings: Settings | None = None, logger: logging.Logger | None = None):
        self.journal = journal
        self.settings = settings or get_settings()
        self.logger = logger or logging.getLogger(__name__)

    def bucket_for_entry(self, entry: SignalJournalEntry, group_by: AttributionGroupBy) -> str:
        if group_by == AttributionGroupBy.SYMBOL: return entry.symbol
        if group_by == AttributionGroupBy.STRATEGY: return entry.strategy_name
        if group_by == AttributionGroupBy.REGIME: return entry.regime or "UNKNOWN"
        if group_by == AttributionGroupBy.RISK_DECISION: return entry.risk_decision or "UNKNOWN"
        if group_by == AttributionGroupBy.PORTFOLIO_DECISION: return entry.portfolio_decision or "UNKNOWN"
        if group_by == AttributionGroupBy.ML_SCORE_BUCKET:
            score = entry.ml_score
            if score is None: return "NO_SCORE"
            if score < 40: return "0-40"
            if score < 55: return "40-55"
            if score < 70: return "55-70"
            if score < 85: return "70-85"
            return "85-100"
        return "ALL"

    def calculate_bucket_metrics(self, entries: list[SignalJournalEntry], group_key: str, group_by: AttributionGroupBy) -> AttributionBucket:
        count = len(entries)
        wins = sum(1 for e in entries if e.outcome == ResearchSignalOutcome.POSITIVE)
        losses = sum(1 for e in entries if e.outcome == ResearchSignalOutcome.NEGATIVE)
        tracked = wins + losses
        win_rate = (wins / tracked * 100) if tracked > 0 else None

        returns = [e.outcome_return_pct for e in entries if e.outcome_return_pct is not None]
        avg_ret = sum(returns) / len(returns) if returns else None
        med_ret = sorted(returns)[len(returns)//2] if returns else None
        total_pnl = sum(returns) if returns else None

        scores = [e.signal_score for e in entries if e.signal_score is not None]
        avg_score = sum(scores) / len(scores) if scores else None

        confidences = [e.confidence for e in entries if e.confidence is not None]
        avg_conf = sum(confidences) / len(confidences) if confidences else None

        return AttributionBucket(
            group_key=group_key,
            group_by=group_by,
            count=count,
            win_rate=win_rate,
            average_return_pct=avg_ret,
            median_return_pct=med_ret,
            total_pnl=total_pnl,
            average_score=avg_score,
            average_confidence=avg_conf
        )

    def build_findings(self, report: AttributionReport) -> list[str]:
        findings = []
        best_bucket = None
        worst_bucket = None
        for b in report.buckets:
            if b.win_rate is not None:
                if best_bucket is None or b.win_rate > (best_bucket.win_rate or -1): best_bucket = b
                if worst_bucket is None or b.win_rate < (worst_bucket.win_rate or 101): worst_bucket = b

        if best_bucket: findings.append(f"Highest win rate in {best_bucket.group_key} ({best_bucket.win_rate:.1f}%)")
        if worst_bucket: findings.append(f"Lowest win rate in {worst_bucket.group_key} ({worst_bucket.win_rate:.1f}%)")
        return findings

    def build_attribution_from_journal(self, entries: list[SignalJournalEntry], group_by: AttributionGroupBy) -> AttributionReport:
        if not entries:
            raise ResearchAttributionError("No journal entries provided for attribution.")

        grouped = {}
        for e in entries:
            key = self.bucket_for_entry(e, group_by)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(e)

        buckets = []
        for key, group_entries in grouped.items():
            buckets.append(self.calculate_bucket_metrics(group_entries, key, group_by))

        report = AttributionReport(
            attribution_id=f"attr_{uuid.uuid4().hex[:8]}",
            group_by=group_by,
            buckets=buckets,
            source_journal_ids=[e.journal_id for e in entries]
        )
        report.findings = self.build_findings(report)
        return report

    def build_attribution_from_paper(self, account_id: str | None = None, group_by: AttributionGroupBy = AttributionGroupBy.SYMBOL) -> AttributionReport:
        # Currently Paper uses generic signal tracking or its own ledger.
        # Fallback to journal entries that are related to paper trading
        # (Where paper_order_id is set)
        entries = self.journal.storage.load_journal_entries(limit=5000)
        paper_entries = [e for e in entries if e.paper_order_id]
        if not paper_entries:
            raise ResearchAttributionError("No paper-related journal entries found.")
        return self.build_attribution_from_journal(paper_entries, group_by)
