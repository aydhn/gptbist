import argparse
from typing import List, Optional
import json

from bist_signal_bot.config.settings import get_settings
from bist_signal_bot.app.research_orchestrator_app import (
    create_research_campaign_registry,
    create_research_run_planner,
    create_research_dag_builder,
    create_research_run_executor,
    create_research_orchestrator_guardrails,
    create_research_run_manifest_builder,
    create_research_orchestrator_store,
    create_research_run_replay_engine
)
from bist_signal_bot.research_orchestrator.models import ResearchCampaignType, ResearchExecutionMode
from bist_signal_bot.research_orchestrator.reporting import format_orchestrator_report_markdown

def get_parser():
    parser = argparse.ArgumentParser(description="Research Orchestrator CLI")
    subparsers = parser.add_subparsers(dest="command")

    # campaigns
    camp_parser = subparsers.add_parser("campaigns")
    camp_parser.add_argument("action", nargs="?", default="list")
    camp_parser.add_argument("name", nargs="?", default=None)
    camp_parser.add_argument("--json", action="store_true")

    # plan
    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("--campaign", required=True)
    plan_parser.add_argument("--symbols", nargs="+")
    plan_parser.add_argument("--strategies", nargs="+")
    plan_parser.add_argument("--models", nargs="+")
    plan_parser.add_argument("--dry-run", action="store_true")
    plan_parser.add_argument("--json", action="store_true")

    # dag
    dag_parser = subparsers.add_parser("dag")
    dag_parser.add_argument("--campaign", required=True)
    dag_parser.add_argument("--mermaid", action="store_true")

    # run
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--campaign")
    run_parser.add_argument("--plan-id")
    run_parser.add_argument("--symbols", nargs="+")
    run_parser.add_argument("--strategies", nargs="+")
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.add_argument("--save", action="store_true")
    run_parser.add_argument("--json", action="store_true")

    # status
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--json", action="store_true")

    # show
    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("run_id")
    show_parser.add_argument("--json", action="store_true")

    # manifest
    manifest_parser = subparsers.add_parser("manifest")
    manifest_parser.add_argument("run_id")
    manifest_parser.add_argument("--json", action="store_true")

    # replay
    replay_parser = subparsers.add_parser("replay")
    replay_parser.add_argument("--manifest-id", required=True)
    replay_parser.add_argument("--dry-run", action="store_true")
    replay_parser.add_argument("--json", action="store_true")

    # guardrails
    guard_parser = subparsers.add_parser("guardrails")
    guard_parser.add_argument("--campaign")
    guard_parser.add_argument("--plan-id")
    guard_parser.add_argument("--json", action="store_true")

    # report
    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--latest", action="store_true")
    report_parser.add_argument("--json", action="store_true")

    # recent
    recent_parser = subparsers.add_parser("recent")
    recent_parser.add_argument("--limit", type=int, default=10)
    recent_parser.add_argument("--json", action="store_true")

    # config
    config_parser = subparsers.add_parser("config")
    config_parser.add_argument("--json", action="store_true")

    return parser

def main(args: list[str] | None = None):
    parser = get_parser()
    parsed = parser.parse_args(args)

    settings = get_settings()

    if parsed.command == "campaigns":
        registry = create_research_campaign_registry(settings)
        if parsed.action == "show" and parsed.name:
            camp = registry.get_campaign(parsed.name)
            if not camp:
                print(f"Campaign {parsed.name} not found.")
                return 1
            if parsed.json:
                print(camp.model_dump_json())
            else:
                print(registry.render_campaign_markdown(camp))
        else:
            camps = registry.default_campaigns()
            if parsed.json:
                print(json.dumps([c.model_dump(mode="json") for c in camps]))
            else:
                for c in camps:
                    print(f"- {c.name} ({c.campaign_type.value})")

    elif parsed.command == "plan":
        planner = create_research_run_planner(settings)
        try:
            ctype = ResearchCampaignType(parsed.campaign)
        except ValueError:
            ctype = ResearchCampaignType.CUSTOM

        mode = ResearchExecutionMode.DRY_RUN if parsed.dry_run else ResearchExecutionMode.LOCAL_EXECUTE
        plan = planner.create_plan(
            campaign_type=ctype,
            symbols=parsed.symbols,
            strategies=parsed.strategies,
            models=parsed.models,
            execution_mode=mode
        )
        if parsed.json:
            print(plan.model_dump_json())
        else:
            print(f"Created Plan: {plan.plan_id}")
            print(f"Tasks: {len(plan.tasks)}")
            print(f"Disclaimer: {plan.disclaimer}")

    elif parsed.command == "run":
        planner = create_research_run_planner(settings)
        executor = create_research_run_executor(settings)
        store = create_research_orchestrator_store(settings)

        if parsed.plan_id:
            plan = store.get_plan(parsed.plan_id)
            if not plan:
                print("Plan not found.")
                return 1
        else:
            try:
                ctype = ResearchCampaignType(parsed.campaign)
            except ValueError:
                ctype = ResearchCampaignType.CUSTOM
            plan = planner.create_plan(
                campaign_type=ctype,
                symbols=parsed.symbols,
                strategies=parsed.strategies
            )

        run = executor.execute_plan(plan, dry_run=parsed.dry_run, save=parsed.save)

        if parsed.save:
            store.append_run(run)

        if parsed.json:
            print(run.model_dump_json())
        else:
            print(f"Run {run.run_id} completed with status {run.status.value}")

    elif parsed.command == "dag":
        planner = create_research_run_planner(settings)
        dag = create_research_dag_builder(settings)
        try:
            ctype = ResearchCampaignType(parsed.campaign)
        except ValueError:
            ctype = ResearchCampaignType.CUSTOM
        plan = planner.create_plan(campaign_type=ctype)

        if parsed.mermaid:
            print(dag.render_mermaid(plan))
        else:
            levels = dag.task_levels(plan.tasks, plan.dependencies)
            for i, lvl in enumerate(levels):
                print(f"Level {i}: {[t.task_id for t in lvl]}")

    else:
        # For mock purposes, just print command
        print(f"Mock executed: {parsed.command}")

    return 0

if __name__ == "__main__":
    main()
