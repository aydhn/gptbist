import argparse
from typing import Any

from bist_signal_bot.app.scheduler_app import create_scheduler_orchestrator
# A simple mock settings to prevent needing to load full app config for quick commands
class CLISettings:
    DATA_DIR = "data"
    SCHEDULER_GLOBAL_LOCK_TTL_SECONDS = 3600
    SCHEDULER_JOB_LOCK_TTL_SECONDS = 1800
    SCHEDULER_DEDUPE_WINDOW_MINUTES = 30
    SCHEDULER_RUN_DUE_LIMIT = 10
    SCHEDULER_REQUIRE_GOVERNANCE_GATE = True

def handle_scheduler(args: argparse.Namespace) -> None:
    print("Scheduler CLI commands are partially implemented.")

    settings = CLISettings()
    orchestrator = create_scheduler_orchestrator(settings)

    if args.subcommand == "list":
        jobs = orchestrator.list_jobs(enabled_only=getattr(args, 'enabled_only', False))
        for j in jobs:
            print(f"- {j.job_id} ({j.name}): {j.enabled}")

    elif args.subcommand == "defaults":
        if getattr(args, 'create', False) and getattr(args, 'confirm', False):
            defaults = orchestrator.default_jobs()
            for j in defaults:
                orchestrator.add_job(j, confirm=True)
            print(f"Created {len(defaults)} default jobs.")
        else:
            defaults = orchestrator.default_jobs()
            print(f"Would create {len(defaults)} default jobs. Use --create --confirm")

    elif args.subcommand == "due":
        # Simplified
        res = orchestrator.run_due(dry_run=True)
        print(f"Due jobs checked. Run returned status {res.status.value}")
        if res.due_result:
            print(f"Found {len(res.due_result.due_jobs)} due jobs")

    elif args.subcommand == "run-due":
        dry_run = getattr(args, 'dry_run', False)
        confirm = getattr(args, 'confirm', False)
        if not dry_run and not confirm:
            print("Must use --dry-run or --confirm")
            return

        res = orchestrator.run_due(dry_run=dry_run)
        print(f"Run-due completed with status {res.status.value}")
        print(f"Success: {res.success_count}, Failed: {res.failed_count}")

    else:
        print(f"Unknown subcommand {args.subcommand}")
