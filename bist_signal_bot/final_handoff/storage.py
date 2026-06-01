import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_final_handoff_dir
from bist_signal_bot.final_handoff.models import (
    FinalHandoffManifest,
    FinalReleasePack,
    OperatorPlaybook,
    DeveloperPlaybook,
    FinalCommandMapEntry,
    FinalModuleSummary,
    PostReleaseRoadmapItem,
    MaintenanceTask,
    FinalHandoffReport
)

class FinalHandoffStore:
    def __init__(self, settings: Settings | None = None, base_dir: Path | None = None):
        self.settings = settings
        if base_dir:
            self.base_dir = base_dir
        else:
            self.base_dir = get_final_handoff_dir(settings)

        self.manifests_path = self.base_dir / "manifests" / "final_handoff_manifests.jsonl"
        self.release_packs_path = self.base_dir / "release_pack" / "final_release_packs.jsonl"
        self.operator_playbooks_path = self.base_dir / "operator" / "operator_playbooks.jsonl"
        self.developer_playbooks_path = self.base_dir / "developer" / "developer_playbooks.jsonl"
        self.command_map_path = self.base_dir / "command_map" / "final_command_map.json"
        self.module_map_path = self.base_dir / "module_map" / "final_module_map.json"
        self.roadmap_path = self.base_dir / "roadmap" / "post_release_roadmap.json"
        self.maintenance_path = self.base_dir / "maintenance" / "maintenance_tasks.json"
        self.reports_dir = self.base_dir / "reports"

        self.manifests_path.parent.mkdir(parents=True, exist_ok=True)
        self.release_packs_path.parent.mkdir(parents=True, exist_ok=True)
        self.operator_playbooks_path.parent.mkdir(parents=True, exist_ok=True)
        self.developer_playbooks_path.parent.mkdir(parents=True, exist_ok=True)
        self.command_map_path.parent.mkdir(parents=True, exist_ok=True)
        self.module_map_path.parent.mkdir(parents=True, exist_ok=True)
        self.roadmap_path.parent.mkdir(parents=True, exist_ok=True)
        self.maintenance_path.parent.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _append_jsonl(self, path: Path, data: dict) -> Path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, default=str) + "\n")
        return path

    def _load_latest_jsonl(self, path: Path) -> Optional[dict]:
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return None
            return json.loads(lines[-1])

    def append_manifest(self, manifest: FinalHandoffManifest) -> Path:
        return self._append_jsonl(self.manifests_path, manifest.model_dump())

    def load_latest_manifest(self) -> Optional[FinalHandoffManifest]:
        data = self._load_latest_jsonl(self.manifests_path)
        return FinalHandoffManifest(**data) if data else None

    def append_release_pack(self, pack: FinalReleasePack) -> Path:
        return self._append_jsonl(self.release_packs_path, pack.model_dump())

    def load_latest_release_pack(self) -> Optional[FinalReleasePack]:
        data = self._load_latest_jsonl(self.release_packs_path)
        return FinalReleasePack(**data) if data else None

    def append_operator_playbook(self, playbook: OperatorPlaybook) -> Path:
        return self._append_jsonl(self.operator_playbooks_path, playbook.model_dump())

    def load_latest_operator_playbook(self) -> Optional[OperatorPlaybook]:
        data = self._load_latest_jsonl(self.operator_playbooks_path)
        return OperatorPlaybook(**data) if data else None

    def append_developer_playbook(self, playbook: DeveloperPlaybook) -> Path:
        return self._append_jsonl(self.developer_playbooks_path, playbook.model_dump())

    def load_latest_developer_playbook(self) -> Optional[DeveloperPlaybook]:
        data = self._load_latest_jsonl(self.developer_playbooks_path)
        return DeveloperPlaybook(**data) if data else None

    def save_command_map(self, entries: list[FinalCommandMapEntry]) -> Path:
        with open(self.command_map_path, "w", encoding="utf-8") as f:
            json.dump([e.model_dump() for e in entries], f, indent=2, default=str)
        return self.command_map_path

    def load_command_map(self) -> list[FinalCommandMapEntry]:
        if not self.command_map_path.exists():
            return []
        with open(self.command_map_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [FinalCommandMapEntry(**item) for item in data]

    def save_module_map(self, modules: list[FinalModuleSummary]) -> Path:
        with open(self.module_map_path, "w", encoding="utf-8") as f:
            json.dump([m.model_dump() for m in modules], f, indent=2, default=str)
        return self.module_map_path

    def load_module_map(self) -> list[FinalModuleSummary]:
        if not self.module_map_path.exists():
            return []
        with open(self.module_map_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [FinalModuleSummary(**item) for item in data]

    def save_roadmap(self, items: list[PostReleaseRoadmapItem]) -> Path:
        with open(self.roadmap_path, "w", encoding="utf-8") as f:
            json.dump([i.model_dump() for i in items], f, indent=2, default=str)
        return self.roadmap_path

    def load_roadmap(self) -> list[PostReleaseRoadmapItem]:
        if not self.roadmap_path.exists():
            return []
        with open(self.roadmap_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [PostReleaseRoadmapItem(**item) for item in data]

    def save_maintenance_tasks(self, tasks: list[MaintenanceTask]) -> Path:
        with open(self.maintenance_path, "w", encoding="utf-8") as f:
            json.dump([t.model_dump() for t in tasks], f, indent=2, default=str)
        return self.maintenance_path

    def load_maintenance_tasks(self) -> list[MaintenanceTask]:
        if not self.maintenance_path.exists():
            return []
        with open(self.maintenance_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [MaintenanceTask(**item) for item in data]

    def save_report(self, report: FinalHandoffReport, markdown_text: str) -> dict[str, Path]:
        date_str = datetime.now().strftime("%Y%m%d")
        report_dir = self.reports_dir / date_str
        report_dir.mkdir(parents=True, exist_ok=True)

        md_path = report_dir / "final_handoff_report.md"
        json_path = report_dir / "final_handoff_report.json"

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2, default=str)

        return {"markdown": md_path, "json": json_path}
