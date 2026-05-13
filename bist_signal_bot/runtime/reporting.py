import pandas as pd
from typing import Dict, Any, List

from bist_signal_bot.runtime.models import RuntimePipelineResult, RuntimeJobResult, RuntimeState

def runtime_pipeline_result_to_dict(result: RuntimePipelineResult) -> Dict[str, Any]:
    return result.model_dump()

def runtime_jobs_to_dataframe(jobs: List[RuntimeJobResult]) -> pd.DataFrame:
    data = []
    for job in jobs:
        data.append({
            "job_id": job.job_id,
            "type": job.job_type.value,
            "status": job.status.value,
            "attempts": job.attempts,
            "elapsed_sec": job.elapsed_seconds,
            "issues": len(job.issues)
        })
    return pd.DataFrame(data)

def format_runtime_result_text(result: RuntimePipelineResult) -> str:
    lines = [
        f"--- Runtime Pipeline Result ---",
        f"Run ID: {result.run_id}",
        f"Status: {result.status.value}",
        f"Strategy: {result.config.strategy_name}",
        f"Elapsed: {result.elapsed_seconds:.2f}s",
        f"Jobs: {result.success_count()}/{len(result.job_results)} successful",
        f"Disclaimer: {result.disclaimer}",
        f"No real order sent."
    ]
    return "\n".join(lines)

def format_runtime_markdown(result: RuntimePipelineResult) -> str:
    lines = [
        f"# Runtime Pipeline Report",
        f"**Run ID:** {result.run_id}",
        f"**Status:** {result.status.value}",
        f"**Strategy:** {result.config.strategy_name}",
        f"**Disclaimer:** {result.disclaimer}",
        f"",
        f"## Jobs",
        f"| Type | Status | Elapsed |",
        f"|---|---|---|"
    ]
    for job in result.job_results:
        lines.append(f"| {job.job_type.value} | {job.status.value} | {job.elapsed_seconds:.2f}s |")

    return "\n".join(lines)

def format_runtime_status_text(state: RuntimeState) -> str:
    last_status_str = state.last_status.value if state.last_status else 'N/A'
    return "\n".join([
        f"Runtime Status:",
        f"Is Running: {state.is_running}",
        f"Last Status: {last_status_str}",
        f"Total Runs: {state.total_runs}",
        f"Success: {state.success_runs}",
        f"Failed: {state.failed_runs}",
        f"Consecutive Failures: {state.consecutive_failures}"
    ])