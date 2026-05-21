import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from bist_signal_bot.research_lab.models import ResearchJob, ResearchJobResult, ResearchBatchPlan, ResearchBatchRun, ResearchLabPolicy
from bist_signal_bot.config.settings import Settings
from bist_signal_bot.storage.paths import get_research_lab_dir
from bist_signal_bot.core.exceptions import ResearchLabStorageError

class ResearchLabStore:
    def __init__(self, settings: Optional[Settings] = None, base_dir: Optional[Path] = None):
        self.settings = settings
        self.base_dir = base_dir or get_research_lab_dir(settings)
        self.jobs_dir = self.base_dir / "jobs"
        self.results_dir = self.base_dir / "results"
        self.plans_dir = self.base_dir / "plans"
        self.runs_dir = self.base_dir / "runs"
        self.policy_dir = self.base_dir / "policy"

        for d in [self.jobs_dir, self.results_dir, self.plans_dir, self.runs_dir, self.policy_dir]:
            d.mkdir(parents=True, exist_ok=True)

        self.jobs_file = self.jobs_dir / "jobs.jsonl"
        self.results_file = self.results_dir / "results.jsonl"

    def append_job(self, job: ResearchJob) -> Path:
        with open(self.jobs_file, "a", encoding="utf-8") as f:
            f.write(job.json() + "\n")
        return self.jobs_file

    def load_jobs(self, limit: int = 1000) -> List[ResearchJob]:
        if not self.jobs_file.exists():
            return []
        jobs = []
        with open(self.jobs_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if not line.strip():
                     continue
                try:
                    jobs.append(ResearchJob.parse_raw(line))
                    if len(jobs) >= limit:
                        break
                except Exception:
                    pass
        unique = {}
        for j in jobs:
            if j.job_id not in unique:
                 unique[j.job_id] = j
        return list(unique.values())

    def update_job(self, job: ResearchJob) -> Path:
        job.updated_at = datetime.utcnow()
        return self.append_job(job)

    def append_result(self, result: ResearchJobResult) -> Path:
        with open(self.results_file, "a", encoding="utf-8") as f:
            f.write(result.json() + "\n")
        return self.results_file

    def load_results(self, limit: int = 1000) -> List[ResearchJobResult]:
        if not self.results_file.exists():
            return []
        results = []
        with open(self.results_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in reversed(lines):
                if not line.strip():
                     continue
                try:
                    results.append(ResearchJobResult.parse_raw(line))
                    if len(results) >= limit:
                        break
                except Exception:
                    pass
        return results

    def save_plan(self, plan: ResearchBatchPlan) -> Dict[str, Path]:
        date_str = plan.created_at.strftime("%Y%m%d")
        plan_dir = self.plans_dir / date_str / plan.plan_id
        plan_dir.mkdir(parents=True, exist_ok=True)
        plan_file = plan_dir / "batch_plan.json"
        with open(plan_file, "w", encoding="utf-8") as f:
             f.write(plan.json())
        return {"plan": plan_file}

    def load_plan(self, plan_id: str) -> Optional[ResearchBatchPlan]:
        for p in self.plans_dir.rglob("batch_plan.json"):
            if p.parent.name == plan_id:
                try:
                    with open(p, "r", encoding="utf-8") as f:
                         return ResearchBatchPlan.parse_raw(f.read())
                except Exception:
                    return None
        return None

    def save_batch_run(self, run: ResearchBatchRun) -> Dict[str, Path]:
        date_str = run.started_at.strftime("%Y%m%d")
        run_dir = self.runs_dir / date_str / run.batch_id
        run_dir.mkdir(parents=True, exist_ok=True)
        run_file = run_dir / "batch_run.json"
        with open(run_file, "w", encoding="utf-8") as f:
             f.write(run.json())
        return {"run": run_file}

    def load_batch_run(self, batch_id: str) -> Optional[ResearchBatchRun]:
        for p in self.runs_dir.rglob("batch_run.json"):
            if p.parent.name == batch_id:
                try:
                    with open(p, "r", encoding="utf-8") as f:
                         return ResearchBatchRun.parse_raw(f.read())
                except Exception:
                    return None
        return None

    def list_recent_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        runs = []
        files = list(self.runs_dir.rglob("batch_run.json"))
        files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        for p in files[:limit]:
            try:
                with open(p, "r", encoding="utf-8") as f:
                     run = ResearchBatchRun.parse_raw(f.read())
                     runs.append(run.summary())
            except Exception:
                pass
        return runs

    def save_policy(self, policy: ResearchLabPolicy) -> Path:
        pol_file = self.policy_dir / "research_lab_policy.json"
        with open(pol_file, "w", encoding="utf-8") as f:
             f.write(policy.json())
        return pol_file

    def load_policy(self) -> Optional[ResearchLabPolicy]:
        pol_file = self.policy_dir / "research_lab_policy.json"
        if pol_file.exists():
            try:
                 with open(pol_file, "r", encoding="utf-8") as f:
                      return ResearchLabPolicy.parse_raw(f.read())
            except Exception:
                 pass
        return None
