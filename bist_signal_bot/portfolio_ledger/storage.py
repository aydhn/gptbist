import json
from pathlib import Path
from typing import Any
from pydantic import BaseModel
from datetime import datetime, timezone

from bist_signal_bot.portfolio_ledger.models import (
    ResearchPortfolio,
    ResearchPortfolioStatus,
    PortfolioLedgerEvent,
    PortfolioValuationSnapshot,
    PortfolioAttributionResult,
    PortfolioOutcomeResult,
    RebalanceTrackingResult,
    PortfolioNavPoint,
    PortfolioLedgerReport
)
from bist_signal_bot.core.exceptions import PortfolioLedgerStorageError

class PortfolioLedgerStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.portfolios_file = self.base_dir / "portfolios" / "research_portfolios.jsonl"
        self.events_file = self.base_dir / "events" / "portfolio_ledger_events.jsonl"
        self.valuations_file = self.base_dir / "valuations" / "portfolio_valuations.jsonl"
        self.attributions_file = self.base_dir / "attribution" / "portfolio_attributions.jsonl"
        self.outcomes_file = self.base_dir / "outcomes" / "portfolio_outcomes.jsonl"
        self.rebalance_file = self.base_dir / "rebalance" / "rebalance_tracking.jsonl"
        self.nav_file = self.base_dir / "nav" / "portfolio_nav_points.jsonl"
        self.reports_dir = self.base_dir / "reports"

        self._init_dirs()

    def _init_dirs(self):
        for f in [
            self.portfolios_file, self.events_file, self.valuations_file,
            self.attributions_file, self.outcomes_file, self.rebalance_file, self.nav_file
        ]:
            f.parent.mkdir(parents=True, exist_ok=True)
            if not f.exists():
                f.touch()
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _append_jsonl(self, file_path: Path, data: BaseModel):
        try:
            with file_path.open('a', encoding='utf-8') as f:
                f.write(data.model_dump_json() + '\n')
        except Exception as e:
            raise PortfolioLedgerStorageError(f"Failed to append to {file_path}: {e}")

    def append_portfolio(self, portfolio: ResearchPortfolio) -> Path:
        self._append_jsonl(self.portfolios_file, portfolio)
        return self.portfolios_file

    def load_portfolios(self, status: ResearchPortfolioStatus | None = None, limit: int = 1000) -> list[ResearchPortfolio]:
        # Because append-only, we must return the latest state for each portfolio_id
        latest_states = {}
        if not self.portfolios_file.exists():
            return []

        with self.portfolios_file.open('r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                port = ResearchPortfolio(**data)
                latest_states[port.portfolio_id] = port

        results = list(latest_states.values())
        if status:
            results = [r for r in results if r.status == status]

        # sort by updated descending
        results.sort(key=lambda x: x.updated_at, reverse=True)
        return results[:limit]

    def get_portfolio(self, portfolio_id_or_name: str) -> ResearchPortfolio | None:
        portfolios = self.load_portfolios(limit=10000)
        for p in portfolios:
            if p.portfolio_id == portfolio_id_or_name or p.name == portfolio_id_or_name:
                return p
        return None

    def append_event(self, event: PortfolioLedgerEvent) -> Path:
        self._append_jsonl(self.events_file, event)
        return self.events_file

    def load_events(self, portfolio_id: str | None = None, limit: int = 1000) -> list[PortfolioLedgerEvent]:
        events = []
        if not self.events_file.exists():
            return events

        with self.events_file.open('r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                evt = PortfolioLedgerEvent(**data)
                if portfolio_id is None or evt.portfolio_id == portfolio_id:
                    events.append(evt)

        events.sort(key=lambda x: x.created_at, reverse=True)
        return events[:limit]

    def append_valuation(self, snapshot: PortfolioValuationSnapshot) -> Path:
        self._append_jsonl(self.valuations_file, snapshot)
        return self.valuations_file

    def load_latest_valuation(self, portfolio_id: str) -> PortfolioValuationSnapshot | None:
        if not self.valuations_file.exists():
            return None

        latest = None
        with self.valuations_file.open('r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                snap = PortfolioValuationSnapshot(**data)
                if snap.portfolio_id == portfolio_id:
                    if latest is None or snap.generated_at > latest.generated_at:
                        latest = snap
        return latest

    def append_attribution(self, result: PortfolioAttributionResult) -> Path:
        self._append_jsonl(self.attributions_file, result)
        return self.attributions_file

    def load_latest_attribution(self, portfolio_id: str) -> PortfolioAttributionResult | None:
        if not self.attributions_file.exists():
            return None

        latest = None
        with self.attributions_file.open('r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                res = PortfolioAttributionResult(**data)
                if res.portfolio_id == portfolio_id:
                    if latest is None or res.generated_at > latest.generated_at:
                        latest = res
        return latest

    def append_outcome(self, result: PortfolioOutcomeResult) -> Path:
        self._append_jsonl(self.outcomes_file, result)
        return self.outcomes_file

    def load_outcomes(self, portfolio_id: str | None = None, limit: int = 1000) -> list[PortfolioOutcomeResult]:
        outcomes = []
        if not self.outcomes_file.exists():
            return outcomes

        with self.outcomes_file.open('r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                out = PortfolioOutcomeResult(**data)
                if portfolio_id is None or out.portfolio_id == portfolio_id:
                    outcomes.append(out)

        outcomes.sort(key=lambda x: x.generated_at, reverse=True)
        return outcomes[:limit]

    def append_rebalance_tracking(self, result: RebalanceTrackingResult) -> Path:
        self._append_jsonl(self.rebalance_file, result)
        return self.rebalance_file

    def append_nav_points(self, points: list[PortfolioNavPoint]) -> Path:
        for point in points:
            self._append_jsonl(self.nav_file, point)
        return self.nav_file

    def load_nav_points(self, portfolio_id: str, limit: int = 10000) -> list[PortfolioNavPoint]:
        points = []
        if not self.nav_file.exists():
            return points

        with self.nav_file.open('r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                data = json.loads(line)
                pt = PortfolioNavPoint(**data)
                if pt.portfolio_id == portfolio_id:
                    points.append(pt)

        points.sort(key=lambda x: x.timestamp, reverse=True)
        return points[:limit]

    def save_report(self, report: PortfolioLedgerReport, markdown_text: str) -> dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%M%d")
        dir_path = self.reports_dir / date_str
        dir_path.mkdir(parents=True, exist_ok=True)

        md_file = dir_path / f"portfolio_ledger_report_{report.report_id}.md"
        with md_file.open('w', encoding='utf-8') as f:
            f.write(markdown_text)

        json_file = dir_path / f"portfolio_ledger_report_{report.report_id}.json"
        with json_file.open('w', encoding='utf-8') as f:
            f.write(report.model_dump_json(indent=2))

        return {"markdown": md_file, "json": json_file}
