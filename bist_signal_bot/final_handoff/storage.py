import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_final_handoff_dir
from bist_signal_bot.final_handoff.models import (
    FinalHandoffManifest, FinalReleasePack, OperatorPlaybook,
    DeveloperPlaybook, FinalCommandMapEntry, FinalModuleSummary,
    PostReleaseRoadmapItem, MaintenanceTask, FinalHandoffReport
)
from bist_signal_bot.core.exceptions import FinalHandoffStorageError

class FinalHandoffStore:
    def __init__(self, settings: Optional[Settings] = None, base_dir: Optional[Path] = None):
        self.settings = settings or Settings()
        if base_dir:
            self.base_dir = base_dir / self.settings.FINAL_HANDOFF_DIR_NAME
            self.base_dir.mkdir(parents=True, exist_ok=True)
        else:
            self.base_dir = get_final_handoff_dir(self.settings)

    def _append_jsonl(self, file_path: Path, data: dict):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

    def _read_latest_jsonl(self, file_path: Path) -> Optional[dict]:
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                return json.loads(lines[-1])
        return None

    def _write_json(self, file_path: Path, data: List[dict]):
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _read_json(self, file_path: Path) -> List[dict]:
        if not file_path.exists():
            return []
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def append_manifest(self, manifest: FinalHandoffManifest) -> Path:
        try:
            path = self.base_dir / "manifests" / "final_handoff_manifests.jsonl"
            self._append_jsonl(path, manifest.model_dump(mode="json"))
            return path
        except Exception as e:
            raise FinalHandoffStorageError(f"Failed to append manifest: {str(e)}")

    def load_latest_manifest(self) -> Optional[FinalHandoffManifest]:
        try:
            path = self.base_dir / "manifests" / "final_handoff_manifests.jsonl"
            data = self._read_latest_jsonl(path)
            if data:
                return FinalHandoffManifest(**data)
            return None
        except Exception as e:
            raise FinalHandoffStorageError(f"Failed to load latest manifest: {str(e)}")

    def append_release_pack(self, pack: FinalReleasePack) -> Path:
        try:
            path = self.base_dir / "release_pack" / "final_release_packs.jsonl"
            self._append_jsonl(path, pack.model_dump(mode="json"))
            return path
        except Exception as e:
            raise FinalHandoffStorageError(f"Failed to append release pack: {str(e)}")

    def load_latest_release_pack(self) -> Optional[FinalReleasePack]:
        try:
            path = self.base_dir / "release_pack" / "final_release_packs.jsonl"
            data = self._read_latest_jsonl(path)
            if data:
                return FinalReleasePack(**data)
            return None
        except Exception as e:
            raise FinalHandoffStorageError(f"Failed to load latest release pack: {str(e)}")

    def append_operator_playbook(self, playbook: OperatorPlaybook) -> Path:
        try:
            path = self.base_dir / "operator" / "operator_playbooks.jsonl"
            self._append_jsonl(path, playbook.model_dump(mode="json"))
            return path
        except Exception as e:
            raise FinalHandoffStorageError(f"Failed to append operator playbook: {str(e)}")

    def load_latest_operator_playbook(self) -> Optional[OperatorPlaybook]:
        try:
            path = self.base_dir / "operator" / "operator_playbooks.jsonl"
            data = self._read_latest_jsonl(path)
            if data:
                return OperatorPlaybook(**data)
            return None
        except Exception as e:
            raise FinalHandoffStorageError(f"Failed to load latest operator playbook: {str(e)}")

    def append_developer_playbook(self, playbook: DeveloperPlaybook) -> Path:
        try:
            path = self.base_dir / "developer" / "developer_playbooks.jsonl"
            self._append_jsonl(path, playbook.model_dump(mode="json"))
            return path
        except Exception as e:
            raise FinalHandoffStorageError(f"Failed to append developer playbook: {str(e)}")

    def load_latest_developer_playbook(self) -> Optional[DeveloperPlaybook]:
        try:
            path = self.base_dir / "developer" / "developer_playbooks.jsonl"
            data = self._read_latest_jsonl(path)
            if data:
                return DeveloperPlaybook(**data)
            return None
        except Exception as e:
            raise FinalHandoffStorageError(f"Failed to load latest developer playbook: {str(e)}")

    def save_command_map(self, entries: List[FinalCommandMapEntry]) -> Path:
        try:
            path = self.base_dir / "command_map" / "final_command_map.json"
            self._write_json(path, [e.model_dump(mode="json") for e in entries])
            return path
        except Exception as e:
             raise FinalHandoffStorageError(f"Failed to save command map: {str(e)}")

    def load_command_map(self) -> List[FinalCommandMapEntry]:
        try:
            path = self.base_dir / "command_map" / "final_command_map.json"
            data = self._read_json(path)
            return [FinalCommandMapEntry(**d) for d in data]
        except Exception as e:
            raise FinalHandoffStorageError(f"Failed to load command map: {str(e)}")

    def save_module_map(self, modules: List[FinalModuleSummary]) -> Path:
        try:
             path = self.base_dir / "module_map" / "final_module_map.json"
             self._write_json(path, [m.model_dump(mode="json") for m in modules])
             return path
        except Exception as e:
             raise FinalHandoffStorageError(f"Failed to save module map: {str(e)}")

    def load_module_map(self) -> List[FinalModuleSummary]:
        try:
            path = self.base_dir / "module_map" / "final_module_map.json"
            data = self._read_json(path)
            return [FinalModuleSummary(**d) for d in data]
        except Exception as e:
            raise FinalHandoffStorageError(f"Failed to load module map: {str(e)}")

    def save_roadmap(self, items: List[PostReleaseRoadmapItem]) -> Path:
        try:
            path = self.base_dir / "roadmap" / "post_release_roadmap.json"
            self._write_json(path, [i.model_dump(mode="json") for i in items])
            return path
        except Exception as e:
             raise FinalHandoffStorageError(f"Failed to save roadmap: {str(e)}")

    def load_roadmap(self) -> List[PostReleaseRoadmapItem]:
        try:
            path = self.base_dir / "roadmap" / "post_release_roadmap.json"
            data = self._read_json(path)
            return [PostReleaseRoadmapItem(**d) for d in data]
        except Exception as e:
            raise FinalHandoffStorageError(f"Failed to load roadmap: {str(e)}")

    def save_maintenance_tasks(self, tasks: List[MaintenanceTask]) -> Path:
         try:
            path = self.base_dir / "maintenance" / "maintenance_tasks.json"
            self._write_json(path, [t.model_dump(mode="json") for t in tasks])
            return path
         except Exception as e:
             raise FinalHandoffStorageError(f"Failed to save maintenance tasks: {str(e)}")

    def load_maintenance_tasks(self) -> List[MaintenanceTask]:
        try:
            path = self.base_dir / "maintenance" / "maintenance_tasks.json"
            data = self._read_json(path)
            return [MaintenanceTask(**d) for d in data]
        except Exception as e:
            raise FinalHandoffStorageError(f"Failed to load maintenance tasks: {str(e)}")

    def save_report(self, report: FinalHandoffReport, markdown_text: str) -> Dict[str, Path]:
        try:
             date_str = datetime.utcnow().strftime("%Y%m%d")
             base_path = self.base_dir / "reports" / date_str
             base_path.mkdir(parents=True, exist_ok=True)

             md_path = base_path / "final_handoff_report.md"
             with open(md_path, "w", encoding="utf-8") as f:
                 f.write(markdown_text)

             json_path = base_path / "final_handoff_report.json"
             with open(json_path, "w", encoding="utf-8") as f:
                 json.dump(report.model_dump(mode="json"), f, indent=2)

             return {"markdown": md_path, "json": json_path}
        except Exception as e:
             raise FinalHandoffStorageError(f"Failed to save final handoff report: {str(e)}")
