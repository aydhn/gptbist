import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional, List, Dict, Any

from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_deployment_dir
from bist_signal_bot.deployment.models import FirstRunResult, SmokeTestResult, OperatorRunbook, DeploymentProfile

class DeploymentStore:
    def __init__(self, settings: Settings, base_dir: Optional[Path] = None):
        self.settings = settings
        self.base_dir = base_dir or get_deployment_dir(self.settings)

    def save_first_run_result(self, result: FirstRunResult) -> Dict[str, Path]:
        date_str = result.started_at.strftime("%Y%m%d")
        path = self.base_dir / "first_run" / date_str / result.first_run_id / "first_run_result.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(result.safe_public_dict(), f, indent=2, ensure_ascii=False)

        # Optional symlink or copy to latest
        latest_path = self.base_dir / "first_run" / "latest_first_run_result.json"
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(result.safe_public_dict(), f, indent=2, ensure_ascii=False)

        return {"first_run_json": path, "latest_json": latest_path}

    def load_latest_first_run_result(self) -> Optional[FirstRunResult]:
        path = self.base_dir / "first_run" / "latest_first_run_result.json"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return FirstRunResult(**data)

    def save_smoke_result(self, result: SmokeTestResult) -> Dict[str, Path]:
        date_str = result.started_at.strftime("%Y%m%d")
        path = self.base_dir / "smoke" / date_str / result.smoke_id / "smoke_result.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

        latest_path = self.base_dir / "smoke" / "latest_smoke_result.json"
        with open(latest_path, "w", encoding="utf-8") as f:
            json.dump(result.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

        return {"smoke_json": path, "latest_json": latest_path}

    def load_latest_smoke_result(self) -> Optional[SmokeTestResult]:
        path = self.base_dir / "smoke" / "latest_smoke_result.json"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return SmokeTestResult(**data)

    def save_runbook(self, runbook: OperatorRunbook, markdown_text: str) -> Dict[str, Path]:
        date_str = runbook.created_at.strftime("%Y%m%d")
        path = self.base_dir / "runbooks" / date_str / runbook.runbook_id / "operator_runbook.md"
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(markdown_text)

        json_path = path.with_suffix(".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(runbook.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

        return {"markdown": path, "json": json_path}

    def save_profiles(self, profiles: List[DeploymentProfile]) -> Path:
        path = self.base_dir / "profiles" / "deployment_profiles.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        data = [p.model_dump(mode="json") for p in profiles]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return path

    def load_profiles(self) -> List[DeploymentProfile]:
        path = self.base_dir / "profiles" / "deployment_profiles.json"
        if not path.exists():
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [DeploymentProfile(**p) for p in data]

    def list_recent_first_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        # Find all JSONs under first_run directory
        first_run_dir = self.base_dir / "first_run"
        if not first_run_dir.exists():
            return []

        results = []
        for path in first_run_dir.rglob("first_run_result.json"):
            if "latest_first_run_result.json" in str(path):
                continue
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                results.append(data)

        # Sort by started_at descending
        results.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        return results[:limit]
