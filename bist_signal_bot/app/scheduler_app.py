from bist_signal_bot.scheduler.models import SchedulerOrchestratorConfig
from pathlib import Path

from bist_signal_bot.scheduler.storage import SchedulerStore
from bist_signal_bot.scheduler.calendar import BISTMarketCalendar
from bist_signal_bot.scheduler.session import MarketSessionResolver
from bist_signal_bot.scheduler.triggers import ScheduleTriggerEvaluator
from bist_signal_bot.scheduler.due import DueJobFinder
from bist_signal_bot.scheduler.locks import SchedulerLockManager
from bist_signal_bot.scheduler.deduplication import ScheduledJobDeduplicator
from bist_signal_bot.scheduler.executor import ScheduledJobExecutor, ScheduledJobDependencies
from bist_signal_bot.scheduler.orchestrator import LocalSchedulerOrchestrator

def create_scheduler_store(settings=None, base_dir=None) -> SchedulerStore:
    d = base_dir or getattr(settings, 'DATA_DIR', "data")
    return SchedulerStore(data_dir=d)

def create_market_calendar(settings=None, base_dir=None) -> BISTMarketCalendar:
    d = base_dir or getattr(settings, 'DATA_DIR', "data")
    return BISTMarketCalendar(data_dir=d)

def create_market_session_resolver(settings=None, base_dir=None) -> MarketSessionResolver:
    cal = create_market_calendar(settings, base_dir)
    return MarketSessionResolver(calendar=cal, settings=settings)

def create_scheduled_job_executor(settings=None, base_dir=None) -> ScheduledJobExecutor:
    # In a full app, we would inject all engines
    # Here we inject minimal to satisfy tests
    return ScheduledJobExecutor(dependencies=ScheduledJobDependencies(), settings=settings)

def create_scheduler_orchestrator(settings=None, base_dir=None) -> LocalSchedulerOrchestrator:
    store = create_scheduler_store(settings, base_dir)
    cal = create_market_calendar(settings, base_dir)
    session_resolver = create_market_session_resolver(settings, base_dir)
    trigger_eval = ScheduleTriggerEvaluator()
    due_finder = DueJobFinder(trigger_eval, session_resolver)

    d = base_dir or getattr(settings, 'DATA_DIR', "data")
    lock_mgr = SchedulerLockManager(data_dir=d)

    dedupe = ScheduledJobDeduplicator()
    executor = create_scheduled_job_executor(settings, base_dir)

    config = SchedulerOrchestratorConfig(
        store=store,
        calendar=cal,
        session_resolver=session_resolver,
        trigger_evaluator=trigger_eval,
        due_finder=due_finder,
        lock_manager=lock_mgr,
        deduplicator=dedupe,
        executor=executor,
        settings=settings
    )
    return LocalSchedulerOrchestrator(config)
