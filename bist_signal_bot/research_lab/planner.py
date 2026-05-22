import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from bist_signal_bot.research_lab.models import (
    ResearchBatchPlan, ResearchJob, ResearchJobType, ResearchJobPriority,
    ResearchJobTrigger, ResearchJobRiskLevel
)

class ResearchJobPlanner:
    def __init__(self, settings=None, base_dir=None):
        self.settings = settings
        self.base_dir = base_dir

    def build_job(self, job_type: ResearchJobType, symbols: List[str], strategy_name: Optional[str],
                  priority: ResearchJobPriority, trigger: ResearchJobTrigger, metadata: Dict[str, Any]) -> ResearchJob:

        job_id = f"job_{uuid.uuid4().hex[:8]}"
        risk = ResearchJobRiskLevel.SAFE

        if job_type in [ResearchJobType.BACKTEST, ResearchJobType.WALK_FORWARD, ResearchJobType.OPTIMIZATION, ResearchJobType.ML_RETRAIN]:
            risk = ResearchJobRiskLevel.RESOURCE_HEAVY

        if metadata.get('requires_confirm'):
            risk = ResearchJobRiskLevel.REQUIRES_CONFIRM

        cmd_preview = []
        if job_type == ResearchJobType.BACKTEST:
             cmd_preview = ["python", "-m", "bist_signal_bot", "backtest"]
             if symbols:
                 cmd_preview.extend(["--symbols"] + symbols)
             if strategy_name:
                 cmd_preview.extend(["--strategy", strategy_name])

        elif job_type == ResearchJobType.OPTIMIZATION:
             cmd_preview = ["python", "-m", "bist_signal_bot", "optimize"]

        elif job_type == ResearchJobType.DATA_UPDATE:
             cmd_preview = ["python", "-m", "bist_signal_bot", "data", "download"]

        elif job_type == ResearchJobType.DRIFT_CHECK:
             cmd_preview = ["python", "-m", "bist_signal_bot", "drift", "check"]

        return ResearchJob(
            job_id=job_id,
            job_type=job_type,
            priority=priority,
            trigger=trigger,
            title=f"{job_type.value} for {strategy_name or 'system'}",
            symbols=symbols,
            strategy_name=strategy_name,
            risk_level=risk,
            command_preview=cmd_preview,
            metadata=metadata
        )

    def plan_from_adaptive_refresh(self, refresh_plan: Any) -> ResearchBatchPlan:
        jobs = []
        trigger = ResearchJobTrigger.ADAPTIVE_REFRESH_PLAN
        actions = getattr(refresh_plan, 'actions', []) if hasattr(refresh_plan, 'actions') else refresh_plan.get('actions', [])

        for action in actions:
            action_type = action.get('type')
            sym = action.get('symbols', [])
            strat = action.get('strategy')

            job_type = None
            if action_type == "RUN_BACKTEST":
                job_type = ResearchJobType.BACKTEST
            elif action_type == "RUN_OPTIMIZATION":
                job_type = ResearchJobType.OPTIMIZATION
            elif action_type == "RUN_WALK_FORWARD":
                job_type = ResearchJobType.WALK_FORWARD
            elif action_type == "RETRAIN_MODEL":
                job_type = ResearchJobType.ML_RETRAIN
            elif action_type in ["REDUCE_UNIVERSE", "WATCH_ONLY"]:
                job_type = ResearchJobType.CUSTOM

            if job_type:
                jobs.append(self.build_job(job_type, sym, strat, ResearchJobPriority.NORMAL, trigger, action))

        return self._create_plan(jobs, trigger)

    def plan_from_drift_result(self, drift_result: Any) -> ResearchBatchPlan:
        jobs = []
        trigger = ResearchJobTrigger.DRIFT_ACTION
        actions = getattr(drift_result, 'recommended_actions', []) if hasattr(drift_result, 'recommended_actions') else drift_result.get('recommended_actions', [])

        for action in actions:
            action_type = action.get('type')
            sym = action.get('symbols', [])
            strat = action.get('strategy')

            job_type = None
            if action_type == "RETRAIN_MODEL":
                job_type = ResearchJobType.ML_RETRAIN
            elif action_type == "RUN_BACKTEST":
                job_type = ResearchJobType.BACKTEST
            elif action_type == "RUN_OPTIMIZATION":
                job_type = ResearchJobType.OPTIMIZATION
            elif action_type == "REFRESH_FEATURES":
                job_type = ResearchJobType.FEATURE_REFRESH
            elif action_type == "REVIEW_MANUALLY":
                job_type = ResearchJobType.CUSTOM
            elif action_type == "UPDATE_REFERENCE":
                job_type = ResearchJobType.CUSTOM

            if job_type:
                meta = action.copy()
                if action_type == "UPDATE_REFERENCE":
                    meta['requires_confirm'] = True
                jobs.append(self.build_job(job_type, sym, strat, ResearchJobPriority.HIGH, trigger, meta))

        return self._create_plan(jobs, trigger)

    def plan_from_model_refresh(self, recommendations: List[Any]) -> ResearchBatchPlan:
        jobs = []
        trigger = ResearchJobTrigger.MODEL_REFRESH
        for rec in recommendations:
            jobs.append(self.build_job(ResearchJobType.ML_RETRAIN, rec.get('symbols', []), None, ResearchJobPriority.HIGH, trigger, rec))
        return self._create_plan(jobs, trigger)

    def plan_from_signal_decay(self, report: Any) -> ResearchBatchPlan:
        jobs = []
        trigger = ResearchJobTrigger.SIGNAL_DECAY
        jobs.append(self.build_job(ResearchJobType.BACKTEST, [], None, ResearchJobPriority.HIGH, trigger, {}))
        return self._create_plan(jobs, trigger)

    def plan_from_strategy_decay(self, report: Any) -> ResearchBatchPlan:
        jobs = []
        trigger = ResearchJobTrigger.STRATEGY_DECAY
        jobs.append(self.build_job(ResearchJobType.OPTIMIZATION, [], None, ResearchJobPriority.HIGH, trigger, {}))
        return self._create_plan(jobs, trigger)

    def plan_daily_research(self, symbols: List[str], strategies: List[str]) -> ResearchBatchPlan:
        jobs = []
        trigger = ResearchJobTrigger.SCHEDULED
        jobs.append(self.build_job(ResearchJobType.DATA_FRESHNESS_CHECK, symbols, None, ResearchJobPriority.HIGH, trigger, {}))
        jobs.append(self.build_job(ResearchJobType.DRIFT_CHECK, symbols, None, ResearchJobPriority.NORMAL, trigger, {}))
        jobs.append(self.build_job(ResearchJobType.ADAPTIVE_RECOMMEND, symbols, None, ResearchJobPriority.NORMAL, trigger, {}))
        jobs.append(self.build_job(ResearchJobType.REPORT_GENERATE, symbols, None, ResearchJobPriority.NORMAL, trigger, {}))
        return self._create_plan(jobs, trigger)

    def plan_weekly_research(self, symbols: List[str], strategies: List[str]) -> ResearchBatchPlan:
        jobs = []
        trigger = ResearchJobTrigger.SCHEDULED
        jobs.append(self.build_job(ResearchJobType.DATA_UPDATE, symbols, None, ResearchJobPriority.HIGH, trigger, {}))
        for strat in strategies:
             jobs.append(self.build_job(ResearchJobType.BACKTEST, symbols, strat, ResearchJobPriority.NORMAL, trigger, {}))
             jobs.append(self.build_job(ResearchJobType.WALK_FORWARD, symbols, strat, ResearchJobPriority.NORMAL, trigger, {}))
        jobs.append(self.build_job(ResearchJobType.DRIFT_CHECK, symbols, None, ResearchJobPriority.NORMAL, trigger, {}))
        jobs.append(self.build_job(ResearchJobType.STRESS_TEST, symbols, None, ResearchJobPriority.NORMAL, trigger, {}))
        jobs.append(self.build_job(ResearchJobType.REPORT_GENERATE, symbols, None, ResearchJobPriority.NORMAL, trigger, {}))
        return self._create_plan(jobs, trigger)

    def estimate_plan(self, plan: ResearchBatchPlan) -> ResearchBatchPlan:
        total_time = 0.0
        for j in plan.jobs:
            total_time += j.max_runtime_seconds
        plan.estimated_runtime_seconds = total_time
        plan.estimated_memory_mb = 1024.0 * len(plan.jobs)
        return plan

    def _create_plan(self, jobs: List[ResearchJob], trigger: ResearchJobTrigger) -> ResearchBatchPlan:
        plan = ResearchBatchPlan(
            plan_id=f"plan_{uuid.uuid4().hex[:8]}",
            trigger=trigger,
            jobs=jobs
        )
        from bist_signal_bot.research_lab.deduplication import ResearchJobDeduplicator
        deduper = ResearchJobDeduplicator()
        for j in plan.jobs:
             j.dedupe_key = deduper.build_dedupe_key(j)

        from bist_signal_bot.research_lab.dependencies import ResearchJobDependencyResolver
        resolver = ResearchJobDependencyResolver()
        plan.dependency_graph = resolver.build_graph(plan.jobs)

        return self.estimate_plan(plan)

    def retrieve_knowledge_context(self, job: Any, settings: Any = None) -> list:
        try:
            from bist_signal_bot.app.knowledge_app import create_evidence_retriever
            retriever = create_evidence_retriever(settings)
            return retriever.retrieve_for_research_lab_job(job)
        except Exception:
            return []
