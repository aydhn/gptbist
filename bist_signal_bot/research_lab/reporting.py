import pandas as pd
from typing import Any, Dict, List
from bist_signal_bot.research_lab.models import ResearchJob, ResearchJobResult, ResearchBatchPlan, ResearchBatchRun

def research_job_to_dict(job: ResearchJob) -> Dict[str, Any]:
    return job.dict(exclude={"command_preview", "metadata"})

def research_job_result_to_dict(result: ResearchJobResult) -> Dict[str, Any]:
    return result.dict(exclude={"stdout_tail", "stderr_tail", "metadata"})

def batch_plan_to_dict(plan: ResearchBatchPlan) -> Dict[str, Any]:
    return {
        "plan_id": plan.plan_id,
        "trigger": plan.trigger.value,
        "job_count": len(plan.jobs),
        "estimated_runtime_seconds": plan.estimated_runtime_seconds,
        "warnings": len(plan.warnings)
    }

def batch_run_to_dict(run: ResearchBatchRun) -> Dict[str, Any]:
    return run.summary()

def jobs_to_dataframe(jobs: List[ResearchJob]) -> pd.DataFrame:
    data = [research_job_to_dict(j) for j in jobs]
    return pd.DataFrame(data)

def results_to_dataframe(results: List[ResearchJobResult]) -> pd.DataFrame:
    data = [research_job_result_to_dict(r) for r in results]
    return pd.DataFrame(data)

def format_job_text(job: ResearchJob) -> str:
    lines = [
        f"Job: {job.title} ({job.job_id})",
        f"Status: {job.status.value}",
        f"Priority: {job.priority.value}",
        f"Symbols: {','.join(job.symbols) if job.symbols else 'N/A'}"
    ]
    return "\n".join(lines)

def format_batch_plan_text(plan: ResearchBatchPlan) -> str:
    lines = [
        f"Research Batch Plan: {plan.plan_id}",
        f"Trigger: {plan.trigger.value}",
        f"Total Jobs: {len(plan.jobs)}",
        f"Estimated Runtime: {plan.estimated_runtime_seconds or 0:.1f}s",
        f"Estimated Memory: {plan.estimated_memory_mb or 0:.1f}MB",
        f"",
        f"Disclaimer: {plan.disclaimer}"
    ]
    return "\n".join(lines)

def format_batch_run_text(run: ResearchBatchRun) -> str:
    lines = [
        f"Research Batch Run: {run.batch_id}",
        f"Status: {run.status.value}",
        f"Total Jobs: {len(run.jobs)}",
        f"Success: {run.success_count}, Failed: {run.failed_count}, Skipped: {run.skipped_count}",
        f"Elapsed Time: {run.elapsed_seconds:.1f}s",
        f"",
        f"Disclaimer: {run.disclaimer}"
    ]
    return "\n".join(lines)

def format_batch_report_markdown(run: ResearchBatchRun) -> str:
    md = [
        f"# Research Batch Report: {run.batch_id}",
        f"**Status:** {run.status.value}",
        f"**Started At:** {run.started_at}",
        f"**Elapsed Time:** {run.elapsed_seconds:.1f}s",
        f"**Disclaimer:** {run.disclaimer}",
        "",
        "## Summary",
        f"- Total Jobs: {len(run.jobs)}",
        f"- Success: {run.success_count}",
        f"- Failed: {run.failed_count}",
        f"- Skipped: {run.skipped_count}",
        "",
        "## Jobs"
    ]
    for j in run.jobs:
        md.append(f"### {j.title} ({j.job_id})")
        md.append(f"- Status: {j.status.value}")
        md.append(f"- Type: {j.job_type.value}")
        md.append(f"- Symbols: {', '.join(j.symbols) if j.symbols else 'N/A'}")
    return "\n".join(md)
