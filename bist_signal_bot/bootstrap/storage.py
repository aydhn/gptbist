import json
from pathlib import Path
from bist_signal_bot.bootstrap.models import BootstrapInitResult, BootstrapValidationResult, OfflineDemoRun, CommandRecipe, ReleaseBundleManifest, OnboardingGuide, BootstrapReport
from bist_signal_bot.storage.paths import get_bootstrap_dir

class BootstrapStore:
    def __init__(self, settings=None, base_dir: Path | None = None):
        self.base_dir = base_dir or Path.cwd()
        self.b_dir = get_bootstrap_dir(settings) if not base_dir else base_dir / "bootstrap"
        self.b_dir.mkdir(parents=True, exist_ok=True)

    def _append_jsonl(self, filename: str, data: dict) -> Path:
        p = self.b_dir / filename
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, default=str) + "\n")
        return p

    def append_init_result(self, result: BootstrapInitResult) -> Path:
        return self._append_jsonl("init/bootstrap_init_results.jsonl", result.dict())

    def load_latest_init_result(self) -> BootstrapInitResult | None:
        return None

    def append_validation_result(self, result: BootstrapValidationResult) -> Path:
        return self._append_jsonl("validation/bootstrap_validation_results.jsonl", result.dict())

    def load_latest_validation_result(self) -> BootstrapValidationResult | None:
        p = self.b_dir / "validation/bootstrap_validation_results.jsonl"
        if p.exists():
            lines = p.read_text().strip().split("\n")
            if lines and lines[-1]:
                data = json.loads(lines[-1])
                if not data.get("profile_name"): data["profile_name"] = None
                return BootstrapValidationResult(**data)
        return None

    def append_demo_run(self, run: OfflineDemoRun) -> Path:
        return self._append_jsonl("demo/offline_demo_runs.jsonl", run.dict())

    def load_latest_demo_run(self) -> OfflineDemoRun | None:
        p = self.b_dir / "demo/offline_demo_runs.jsonl"
        if p.exists():
            lines = p.read_text().strip().split("\n")
            if lines and lines[-1]:
                return OfflineDemoRun(**json.loads(lines[-1]))
        return None

    def save_recipes(self, recipes: list[CommandRecipe]) -> Path:
        p = self.b_dir / "recipes/command_recipes.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps([r.dict() for r in recipes], default=str))
        return p

    def load_recipes(self) -> list[CommandRecipe]:
        return []

    def append_release_bundle(self, manifest: ReleaseBundleManifest) -> Path:
        return self._append_jsonl("release/release_bundle_manifests.jsonl", manifest.dict())

    def load_latest_release_bundle(self) -> ReleaseBundleManifest | None:
        return None

    def append_onboarding_guide(self, guide: OnboardingGuide) -> Path:
        return self._append_jsonl("onboarding/onboarding_guides.jsonl", guide.dict())

    def save_report(self, report: BootstrapReport, markdown_text: str) -> dict[str, Path]:
        return {}
