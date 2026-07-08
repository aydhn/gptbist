import json
import os
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from bist_signal_bot.markets.models import (
    MarketDefinition, InstrumentDefinition, SymbolMapping,
    MarketCalendarDay, MarketSession, MarketUniverse,
    MarketValidationResult, MarketGovernanceAssessment, MarketRegistryReport
)

logger = logging.getLogger(__name__)

class MarketStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.definitions_dir = self.base_dir / "definitions"
        self.instruments_dir = self.base_dir / "instruments"
        self.symbols_dir = self.base_dir / "symbols"
        self.calendars_dir = self.base_dir / "calendars"
        self.sessions_dir = self.base_dir / "sessions"
        self.universes_dir = self.base_dir / "universes"
        self.validations_dir = self.base_dir / "validations"
        self.governance_dir = self.base_dir / "governance"
        self.reports_dir = self.base_dir / "reports"

        for d in [self.definitions_dir, self.instruments_dir, self.symbols_dir,
                 self.calendars_dir, self.sessions_dir, self.universes_dir,
                 self.validations_dir, self.governance_dir, self.reports_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _append_jsonl(self, path: Path, items: List[Any]):
        with open(path, "a", encoding="utf-8") as f:
            for item in items:
                f.write(item.model_dump_json() + "\n")
        return path

    def _load_jsonl(self, path: Path, model_cls, limit: int = 10000) -> List[Any]:
        if not path.exists():
            return []
        res = []
        with open(path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= limit: break
                try:
                    res.append(model_cls.model_validate_json(line))
                except Exception as e:
                    logger.debug(f"Failed to parse line {i} in {path}: {e}")
        return res

    def save_markets(self, markets: List[MarketDefinition]) -> Path:
        p = self.definitions_dir / "market_definitions.json"
        with open(p, "w", encoding="utf-8") as f:
            json.dump([m.model_dump() for m in markets], f, indent=2)
        return p

    def load_markets(self) -> List[MarketDefinition]:
        p = self.definitions_dir / "market_definitions.json"
        if not p.exists(): return []
        with open(p, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                return [MarketDefinition.model_validate(m) for m in data]
            except Exception as e:
                logger.warning(f"Failed to load markets from {p}: {e}")
                return []

    def append_instruments(self, instruments: List[InstrumentDefinition]) -> Path:
        return self._append_jsonl(self.instruments_dir / "instruments.jsonl", instruments)

    def load_instruments(self, market_id: Optional[str] = None, limit: int = 10000) -> List[InstrumentDefinition]:
        items = self._load_jsonl(self.instruments_dir / "instruments.jsonl", InstrumentDefinition, limit)
        if market_id:
            items = [i for i in items if i.market_id == market_id]
        return items

    def append_symbol_mappings(self, mappings: List[SymbolMapping]) -> Path:
        return self._append_jsonl(self.symbols_dir / "symbol_mappings.jsonl", mappings)

    def append_calendar_days(self, days: List[MarketCalendarDay]) -> Path:
        return self._append_jsonl(self.calendars_dir / "market_calendar_days.jsonl", days)

    def append_sessions(self, sessions: List[MarketSession]) -> Path:
        return self._append_jsonl(self.sessions_dir / "market_sessions.jsonl", sessions)

    def append_universe(self, universe: MarketUniverse) -> Path:
        return self._append_jsonl(self.universes_dir / "market_universes.jsonl", [universe])

    def load_universes(self, market_id: Optional[str] = None, limit: int = 1000) -> List[MarketUniverse]:
        items = self._load_jsonl(self.universes_dir / "market_universes.jsonl", MarketUniverse, limit)
        if market_id:
            items = [i for i in items if i.market_id == market_id]
        return items

    def append_validation(self, result: MarketValidationResult) -> Path:
        return self._append_jsonl(self.validations_dir / "market_validations.jsonl", [result])

    def append_governance(self, assessment: MarketGovernanceAssessment) -> Path:
        return self._append_jsonl(self.governance_dir / "market_governance.jsonl", [assessment])

    def load_latest_governance(self, market_id: str) -> Optional[MarketGovernanceAssessment]:
        items = self._load_jsonl(self.governance_dir / "market_governance.jsonl", MarketGovernanceAssessment, 1000)
        items = [i for i in items if i.market_id == market_id]
        return items[-1] if items else None

    def save_report(self, report: MarketRegistryReport, markdown_text: str) -> Dict[str, Path]:
        day = report.generated_at.strftime("%Y%m%d")
        d = self.reports_dir / day
        d.mkdir(exist_ok=True)

        pj = d / "market_registry_report.json"
        with open(pj, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        pm = d / "market_registry_report.md"
        with open(pm, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        return {"json": pj, "markdown": pm}
