from bist_signal_bot.app.performance_app import create_baseline_manager
from typing import List, Dict, Any
from bist_signal_bot.research_lab.models import ResearchJob, ResearchLabPolicy, ResearchJobRiskLevel

class ResearchBudgetManager:
    def estimate_job_cost(self, job: ResearchJob) -> Dict[str, Any]:
        # Try to pull actual estimates from the performance baseline
        from bist_signal_bot.app.performance_app import create_baseline_manager
        from bist_signal_bot.performance.models import BenchmarkType
        from bist_signal_bot.config.settings import Settings

        try:
            baseline_mgr = create_baseline_manager(Settings())
            baseline = baseline_mgr.load_latest_baseline(BenchmarkType.RESEARCH_LAB_JOB)
            if baseline:
                med_time = baseline.metrics.get("median_elapsed_seconds", 300)
                max_mem = baseline.metrics.get("max_memory_peak_mb", 1024 if job.risk_level == ResearchJobRiskLevel.RESOURCE_HEAVY else 256)
                return {
                    "estimated_runtime": int(med_time),
                    "estimated_memory_mb": int(max_mem),
                    "risk_level": job.risk_level.value,
                    "source": "baseline"
                }
        except Exception:
            pass

        return {
            "estimated_runtime": job.max_runtime_seconds,
            "estimated_memory_mb": 1024 if job.risk_level == ResearchJobRiskLevel.RESOURCE_HEAVY else 256,
            "risk_level": job.risk_level.value,
            "source": "heuristic"
        }


    def estimate_batch_cost(self, jobs: List[ResearchJob]) -> Dict[str, Any]:
        total_time = 0
        max_mem = 0
        heavy_count = 0
        for j in jobs:
            cost = self.estimate_job_cost(j)
            total_time += cost["estimated_runtime"]
            if cost["estimated_memory_mb"] > max_mem:
                max_mem = cost["estimated_memory_mb"]
            if cost["risk_level"] == ResearchJobRiskLevel.RESOURCE_HEAVY.value:
                heavy_count += 1
        return {
            "total_estimated_runtime": total_time,
            "peak_memory_mb": max_mem,
            "heavy_job_count": heavy_count
        }

    def check_budget(self, jobs: List[ResearchJob], policy: ResearchLabPolicy) -> List[str]:
        warnings = []
        cost = self.estimate_batch_cost(jobs)
        if len(jobs) > policy.max_jobs_per_batch:
            warnings.append(f"Batch size {len(jobs)} exceeds max_jobs_per_batch {policy.max_jobs_per_batch}")
        if cost["total_estimated_runtime"] > policy.max_runtime_seconds_per_batch:
            warnings.append(f"Estimated runtime {cost['total_estimated_runtime']}s exceeds max {policy.max_runtime_seconds_per_batch}s")
        if policy.max_memory_mb and cost["peak_memory_mb"] > policy.max_memory_mb:
            warnings.append(f"Estimated peak memory {cost['peak_memory_mb']}MB exceeds max {policy.max_memory_mb}MB")
        if cost["heavy_job_count"] > 0 and policy.require_confirm_for_heavy_jobs:
            warnings.append(f"Batch contains {cost['heavy_job_count']} heavy jobs which may require confirmation")
        return warnings

    def resource_snapshot(self) -> Dict[str, Any]:
        try:
            from bist_signal_bot.performance.resources import get_resource_usage
            return get_resource_usage()
        except ImportError:
            return {"status": "unavailable"}
