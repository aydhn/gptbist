import json
from pathlib import Path
from bist_signal_bot.storage.paths import get_research_orchestrator_dir
from bist_signal_bot.research_orchestrator.models import (
    ResearchCampaign,
    ResearchRunPlan,
    ResearchRun,
    ResearchTaskResult,
    ResearchRunManifest,
    ResearchGuardrailCheck,
    ResearchOrchestratorReport
)
from pydantic import BaseModel

class ResearchOrchestratorStore:
    def __init__(self, settings=None, base_dir: Path | None = None):
        if base_dir:
            self.base_dir = base_dir
        else:
            self.base_dir = get_research_orchestrator_dir(settings)

        self.campaigns_dir = self.base_dir / "campaigns"
        self.plans_dir = self.base_dir / "plans"
        self.runs_dir = self.base_dir / "runs"
        self.tasks_dir = self.base_dir / "tasks"
        self.manifests_dir = self.base_dir / "manifests"
        self.guardrails_dir = self.base_dir / "guardrails"
        self.reports_dir = self.base_dir / "reports"

        for d in [self.campaigns_dir, self.plans_dir, self.runs_dir, self.tasks_dir, self.manifests_dir, self.guardrails_dir, self.reports_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _append_jsonl(self, path: Path, model: BaseModel):
        with open(path, "a") as f:
            f.write(model.model_dump_json() + "\n")

    def _load_jsonl(self, path: Path, model_cls: type, limit: int = 1000) -> list:
        if not path.exists():
            return []
        res = []
        with open(path, "r") as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                if line.strip():
                    res.append(model_cls.model_validate_json(line))
        return res

    def save_campaigns(self, campaigns: list[ResearchCampaign]) -> Path:
        path = self.campaigns_dir / "research_campaigns.json"
        with open(path, "w") as f:
            json.dump([c.model_dump(mode="json") for c in campaigns], f, indent=2)
        return path

    def load_campaigns(self) -> list[ResearchCampaign]:
        path = self.campaigns_dir / "research_campaigns.json"
        if not path.exists():
            return []
        with open(path, "r") as f:
            data = json.load(f)
            return [ResearchCampaign.model_validate(d) for d in data]

    def append_plan(self, plan: ResearchRunPlan) -> Path:
        path = self.plans_dir / "research_run_plans.jsonl"
        self._append_jsonl(path, plan)
        return path

    def load_plans(self, limit: int = 1000) -> list[ResearchRunPlan]:
        path = self.plans_dir / "research_run_plans.jsonl"
        return self._load_jsonl(path, ResearchRunPlan, limit)

    def get_plan(self, plan_id: str) -> ResearchRunPlan | None:
        plans = self.load_plans()
        for p in plans:
            if p.plan_id == plan_id:
                return p
        return None

    def append_run(self, run: ResearchRun) -> Path:
        path = self.runs_dir / "research_runs.jsonl"
        self._append_jsonl(path, run)
        return path

    def load_runs(self, limit: int = 1000) -> list[ResearchRun]:
        path = self.runs_dir / "research_runs.jsonl"
        return self._load_jsonl(path, ResearchRun, limit)

    def get_run(self, run_id: str) -> ResearchRun | None:
        runs = self.load_runs()
        for r in runs:
            if r.run_id == run_id:
                return r
        return None

    def append_task_results(self, results: list[ResearchTaskResult]) -> Path:
        path = self.tasks_dir / "research_task_results.jsonl"
        for r in results:
            self._append_jsonl(path, r)
        return path

    def load_task_results(self, run_id: str | None = None, limit: int = 10000) -> list[ResearchTaskResult]:
        path = self.tasks_dir / "research_task_results.jsonl"
        # Filtering by run_id is omitted for simplicity in this mock
        return self._load_jsonl(path, ResearchTaskResult, limit)

    def append_manifest(self, manifest: ResearchRunManifest) -> Path:
        path = self.manifests_dir / "research_run_manifests.jsonl"
        self._append_jsonl(path, manifest)
        return path

    def load_manifests(self, limit: int = 1000) -> list[ResearchRunManifest]:
        path = self.manifests_dir / "research_run_manifests.jsonl"
        return self._load_jsonl(path, ResearchRunManifest, limit)

    def get_manifest(self, manifest_id: str) -> ResearchRunManifest | None:
        manifests = self.load_manifests()
        for m in manifests:
            if m.manifest_id == manifest_id:
                return m
        return None

    def append_guardrail_checks(self, checks: list[ResearchGuardrailCheck]) -> Path:
        path = self.guardrails_dir / "research_guardrail_checks.jsonl"
        for c in checks:
            self._append_jsonl(path, c)
        return path

    def save_report(self, report: ResearchOrchestratorReport, markdown_text: str) -> dict[str, Path]:
        date_str = report.generated_at.strftime("%Y%m%d")
        report_dir = self.reports_dir / date_str
        report_dir.mkdir(parents=True, exist_ok=True)

        md_path = report_dir / "research_orchestrator_report.md"
        with open(md_path, "w") as f:
            f.write(markdown_text)

        json_path = report_dir / "research_orchestrator_report.json"
        with open(json_path, "w") as f:
            f.write(report.model_dump_json(indent=2))

        return {"markdown": md_path, "json": json_path}
