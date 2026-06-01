import uuid
from datetime import datetime, timezone
from typing import Any

from bist_signal_bot.research_orchestrator.models import (
    ResearchRunPlan,
    ResearchTask,
    ResearchTaskType,
    ResearchCampaignType,
    ResearchExecutionMode,
    ResearchDependency,
    ResearchRunStatus,
    ResearchCampaign
)

class ResearchRunPlanner:
    def create_plan(
        self,
        campaign_type: ResearchCampaignType,
        symbols: list[str] | None = None,
        strategies: list[str] | None = None,
        models: list[str] | None = None,
        feature_sets: list[str] | None = None,
        profile_name: str | None = None,
        execution_mode: ResearchExecutionMode = ResearchExecutionMode.DRY_RUN
    ) -> ResearchRunPlan:

        plan_id = str(uuid.uuid4())
        tasks = self.default_tasks_for_campaign(campaign_type)
        dependencies = self.build_dependencies(tasks)

        warnings = []
        if not symbols:
            warnings.append("Missing symbols: No symbols provided for campaign.")

        plan = ResearchRunPlan(
            plan_id=plan_id,
            campaign_type=campaign_type,
            name=f"{campaign_type.value} Plan",
            created_at=datetime.now(timezone.utc),
            execution_mode=execution_mode,
            profile_name=profile_name,
            symbol_universe=symbols or [],
            strategy_names=strategies or [],
            model_ids=models or [],
            feature_set_ids=feature_sets or [],
            tasks=tasks,
            dependencies=dependencies,
            warnings=warnings
        )
        return plan

    def plan_from_campaign(self, campaign: ResearchCampaign, overrides: dict[str, Any] | None = None) -> ResearchRunPlan:
        overrides = overrides or {}

        symbols = overrides.get("symbols", campaign.default_symbols)
        strategies = overrides.get("strategies", campaign.default_strategies)
        models = overrides.get("models", campaign.default_models)
        feature_sets = overrides.get("feature_sets", campaign.default_feature_sets)
        profile_name = overrides.get("profile_name", campaign.default_profile)
        execution_mode = overrides.get("execution_mode", ResearchExecutionMode.DRY_RUN)

        # Merge default tasks with override tasks if needed, here just keeping default for simplicity or overrides if given
        tasks = overrides.get("tasks", campaign.default_tasks)
        if not tasks:
            tasks = self.default_tasks_for_campaign(campaign.campaign_type)

        dependencies = self.build_dependencies(tasks)

        warnings = list(campaign.warnings)
        if not symbols:
            warnings.append("Missing symbols: No symbols provided for campaign.")

        plan_id = str(uuid.uuid4())

        plan = ResearchRunPlan(
            plan_id=plan_id,
            campaign_type=campaign.campaign_type,
            name=f"{campaign.name} Plan",
            created_at=datetime.now(timezone.utc),
            execution_mode=execution_mode,
            profile_name=profile_name,
            symbol_universe=symbols,
            strategy_names=strategies,
            model_ids=models,
            feature_set_ids=feature_sets,
            tasks=tasks,
            dependencies=dependencies,
            warnings=warnings
        )
        return plan

    def default_tasks_for_campaign(self, campaign_type: ResearchCampaignType) -> list[ResearchTask]:
        tasks = []

        if campaign_type == ResearchCampaignType.QUICK_RESEARCH_SCAN:
            chain = [
                ResearchTaskType.DATA_CATALOG_GATE,
                ResearchTaskType.FEATURE_COMPUTE,
                ResearchTaskType.SCANNER_RUN,
                ResearchTaskType.CONTEXT_FUSION,
                ResearchTaskType.REVIEW_CASE,
                ResearchTaskType.REPORT_BUILD
            ]
        elif campaign_type == ResearchCampaignType.FULL_RESEARCH_PIPELINE:
            chain = [
                ResearchTaskType.DATA_CATALOG_GATE,
                ResearchTaskType.FEATURE_COMPUTE,
                ResearchTaskType.SCANNER_RUN,
                ResearchTaskType.BACKTEST_RUN,
                ResearchTaskType.VALIDATION_RUN,
                ResearchTaskType.CALIBRATION_RUN,
                ResearchTaskType.CONTEXT_FUSION,
                ResearchTaskType.REVIEW_CASE,
                ResearchTaskType.PORTFOLIO_RESEARCH,
                ResearchTaskType.MONITORING_RUN,
                ResearchTaskType.LEADERBOARD_BUILD,
                ResearchTaskType.REPORT_BUILD
            ]
        elif campaign_type == ResearchCampaignType.MODEL_GOVERNANCE_CAMPAIGN:
            chain = [
                ResearchTaskType.DATA_CATALOG_GATE,
                ResearchTaskType.FEATURE_COMPUTE,
                ResearchTaskType.VALIDATION_RUN,
                ResearchTaskType.CALIBRATION_RUN,
                ResearchTaskType.MODEL_GOVERNANCE,
                ResearchTaskType.MONITORING_RUN,
                ResearchTaskType.LEADERBOARD_BUILD,
                ResearchTaskType.REPORT_BUILD
            ]
        elif campaign_type == ResearchCampaignType.QA_OPS_RELEASE_CHECK:
            chain = [
                ResearchTaskType.QA_RELEASE_GATE,
                ResearchTaskType.OPS_READINESS,
                ResearchTaskType.DOCS_HUB_CHECK,
                ResearchTaskType.REPORT_BUILD
            ]
        else:
            # Simple fallback for unknown/custom
            chain = [
                ResearchTaskType.DATA_CATALOG_GATE,
                ResearchTaskType.REPORT_BUILD
            ]

        # Generate linear deterministic dependencies
        prev_id = None
        for i, t_type in enumerate(chain):
            t_id = f"task_{t_type.value.lower()}_{i}"
            task = ResearchTask(
                task_id=t_id,
                task_type=t_type,
                name=f"Run {t_type.value}",
                depends_on=[prev_id] if prev_id else []
            )
            tasks.append(task)
            prev_id = t_id

        return tasks

    def build_dependencies(self, tasks: list[ResearchTask]) -> list[ResearchDependency]:
        deps = []
        for t in tasks:
            for d in t.depends_on:
                deps.append(
                    ResearchDependency(
                        dependency_id=str(uuid.uuid4()),
                        from_task_id=d,
                        to_task_id=t.task_id,
                        status="UNKNOWN"
                    )
                )
        return deps

    def validate_plan(self, plan: ResearchRunPlan) -> list[str]:
        errors = []
        task_ids = {t.task_id for t in plan.tasks}

        for task in plan.tasks:
            for dep in task.depends_on:
                if dep not in task_ids:
                    errors.append(f"Task {task.task_id} depends on non-existent task {dep}")

            if task.command:
                # Basic check, guardrails will do more
                unsafe = ["broker", "order", "live"]
                for term in unsafe:
                    if term in task.command.lower():
                        errors.append(f"Task {task.task_id} contains unsafe command term: {term}")

        return errors

    def safe_plan_summary(self, plan: ResearchRunPlan) -> dict[str, Any]:
        return {
            "plan_id": plan.plan_id,
            "campaign_type": plan.campaign_type.value,
            "status": plan.status.value,
            "task_count": len(plan.tasks),
            "warnings_count": len(plan.warnings),
            "disclaimer": plan.disclaimer
        }
