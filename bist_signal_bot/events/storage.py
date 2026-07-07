import json
from pathlib import Path
from typing import Any

from bist_signal_bot.events.models import (
    MarketEvent, EventWindow, BlackoutPolicy, EventRiskAssessment, EventLink, EventImportResult, EventCalendarSnapshot
)

class EventStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.events_file = self.base_dir / "calendar" / "market_events.jsonl"
        self.windows_file = self.base_dir / "windows" / "event_windows.jsonl"
        self.policies_file = self.base_dir / "policies" / "blackout_policies.json"
        self.assessments_file = self.base_dir / "assessments" / "event_risk_assessments.jsonl"
        self.links_file = self.base_dir / "links" / "event_links.jsonl"
        self._events_cache: dict[str, MarketEvent] | None = None

        for file in [self.events_file, self.windows_file, self.policies_file, self.assessments_file, self.links_file]:
            file.parent.mkdir(parents=True, exist_ok=True)
            if not file.exists():
                if file.suffix == ".json":
                    file.write_text("[]")
                else:
                    file.touch()

    def append_event(self, event: MarketEvent) -> Path:
        with open(self.events_file, "a") as f:
            f.write(event.model_dump_json() + "\n")
        if self._events_cache is not None:
            self._events_cache[event.event_id] = event
        return self.events_file

    def load_events(self, limit: int = 10000) -> list[MarketEvent]:
        events = []
        if not self.events_file.exists():
            return events

        with open(self.events_file, "r") as f:
            for line in f:
                if line.strip():
                    events.append(MarketEvent.model_validate_json(line))
                    if len(events) >= limit:
                        break
        return events

    def get_event(self, event_id: str) -> MarketEvent | None:
        if self._events_cache is None:
            self._events_cache = {ev.event_id: ev for ev in self.load_events()}
        return self._events_cache.get(event_id)

    def append_window(self, window: EventWindow) -> Path:
        with open(self.windows_file, "a") as f:
            f.write(window.model_dump_json() + "\n")
        return self.windows_file

    def load_windows(self, limit: int = 10000) -> list[EventWindow]:
        windows = []
        with open(self.windows_file, "r") as f:
            for line in f:
                if line.strip():
                    windows.append(EventWindow.model_validate_json(line))
                    if len(windows) >= limit:
                        break
        return windows

    def save_policies(self, policies: list[BlackoutPolicy]) -> Path:
        with open(self.policies_file, "w") as f:
            f.write(json.dumps([p.model_dump(mode='json') for p in policies], indent=2))
        return self.policies_file

    def load_policies(self) -> list[BlackoutPolicy]:
        with open(self.policies_file, "r") as f:
            data = json.load(f)
            return [BlackoutPolicy(**p) for p in data]

    def append_assessment(self, assessment: EventRiskAssessment) -> Path:
        with open(self.assessments_file, "a") as f:
            f.write(assessment.model_dump_json() + "\n")
        return self.assessments_file

    def load_assessments(self, symbol: str | None = None, limit: int = 1000) -> list[EventRiskAssessment]:
        assessments = []
        with open(self.assessments_file, "r") as f:
            for line in f:
                if line.strip():
                    ass = EventRiskAssessment.model_validate_json(line)
                    if symbol and ass.symbol != symbol:
                        continue
                    assessments.append(ass)
                    if len(assessments) >= limit:
                        break
        return assessments

    def append_link(self, link: EventLink) -> Path:
        with open(self.links_file, "a") as f:
            f.write(link.model_dump_json() + "\n")
        return self.links_file

    def load_links(self, linked_object_id: str | None = None, limit: int = 1000) -> list[EventLink]:
        links = []
        with open(self.links_file, "r") as f:
            for line in f:
                if line.strip():
                    lnk = EventLink.model_validate_json(line)
                    if linked_object_id and lnk.linked_object_id != linked_object_id:
                        continue
                    links.append(lnk)
                    if len(links) >= limit:
                        break
        return links

    def save_import_result(self, result: EventImportResult) -> dict[str, Path]:
        date_str = result.created_at.strftime("%Y%m%d")
        import_dir = self.base_dir / "imports" / date_str / result.import_id
        import_dir.mkdir(parents=True, exist_ok=True)

        file_path = import_dir / "event_import_result.json"
        with open(file_path, "w") as f:
            f.write(result.model_dump_json(indent=2))

        return {"result_file": file_path}

    def save_report(self, snapshot: EventCalendarSnapshot, markdown_text: str) -> dict[str, Path]:
        date_str = snapshot.created_at.strftime("%Y%m%d")
        report_dir = self.base_dir / "reports" / date_str
        report_dir.mkdir(parents=True, exist_ok=True)

        file_path = report_dir / "event_calendar_report.md"
        with open(file_path, "w") as f:
            f.write(markdown_text)

        return {"report_file": file_path}
