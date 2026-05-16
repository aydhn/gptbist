import logging

from .models import ResearchQuery, ResearchRun, SignalJournalEntry, ResearchRunType
from .ledger import ResearchLedger
from .journal import SignalJournal

class ResearchQueryEngine:
    def __init__(self, ledger: ResearchLedger, journal: SignalJournal, logger: logging.Logger | None = None):
        self.ledger = ledger
        self.journal = journal
        self.logger = logger or logging.getLogger(__name__)

    def query_runs(self, query: ResearchQuery) -> list[ResearchRun]:
        entries = self.ledger.load_entries(limit=query.limit, query=query)
        runs = [e.run for e in entries]
        if query.sort_desc:
            runs.sort(key=lambda r: r.started_at, reverse=True)
        else:
            runs.sort(key=lambda r: r.started_at)
        return runs

    def query_journal(self, symbol: str | None = None, strategy_name: str | None = None, limit: int = 100) -> list[SignalJournalEntry]:
        return self.journal.load_entries(limit=limit, symbol=symbol, strategy_name=strategy_name)

    def find_by_tag(self, tag: str, limit: int = 100) -> list[ResearchRun]:
        query = ResearchQuery(tags=[tag], limit=limit)
        return self.query_runs(query)

    def find_recent_failures(self, limit: int = 20) -> list[ResearchRun]:
        from .models import ResearchRunStatus
        query = ResearchQuery(status=[ResearchRunStatus.FAILED, ResearchRunStatus.PARTIAL_SUCCESS], limit=limit)
        return self.query_runs(query)

    def find_best_by_metric(self, metric: str, run_type: ResearchRunType | None = None, limit: int = 10) -> list[ResearchRun]:
        query = ResearchQuery(run_types=[run_type] if run_type else [], limit=1000)
        runs = self.query_runs(query)

        reverse = True
        if "drawdown" in metric.lower() or "elapsed" in metric.lower() or "error" in metric.lower():
            reverse = False

        def key(r):
            val = r.metrics.get(metric)
            if val is None: return float('-inf') if reverse else float('inf')
            return val

        runs.sort(key=key, reverse=reverse)
        return runs[:limit]
