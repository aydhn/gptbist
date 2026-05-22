import json

from bist_signal_bot.scheduler.models import (
    ScheduledJob,
    ScheduledJobRun,
    SchedulerRunResult,
    MarketSessionSnapshot,
    MarketCalendarDay,
    DueJobResult
)

def format_schedule_list_text(jobs: list[ScheduledJob]) -> str:
    lines = ["Scheduled Jobs List:"]
    for j in jobs:
        status = "ENABLED" if j.enabled else "DISABLED"
        lines.append(f"- {j.job_id} ({j.name}): {status} | Trigger: {j.trigger.trigger_type.value}")
    return "\n".join(lines)

def format_due_result_text(result: DueJobResult) -> str:
    lines = [
        f"Due Job Result ({result.generated_at.isoformat()})",
        f"Session: {result.session_snapshot.session_type.value}",
        f"Due: {len(result.due_jobs)}",
        f"Skipped: {len(result.skipped_jobs)}",
        f"Blocked: {len(result.blocked_jobs)}"
    ]
    return "\n".join(lines)

def format_scheduler_run_text(result: SchedulerRunResult) -> str:
    lines = [
        f"Scheduler Run {result.scheduler_run_id}",
        f"Status: {result.status.value}",
        f"Success: {result.success_count}, Failed: {result.failed_count}",
        "---",
        result.disclaimer
    ]
    return "\n".join(lines)

def format_market_session_text(snapshot: MarketSessionSnapshot) -> str:
    lines = [
        f"Market Session ({snapshot.local_date})",
        f"Day Type: {snapshot.day_type.value}",
        f"Session Type: {snapshot.session_type.value}",
        f"Market Open: {snapshot.market_open}"
    ]
    return "\n".join(lines)
