from pathlib import Path

from bist_signal_bot.config.settings import Settings, get_settings
from bist_signal_bot.release.checks import ReleaseCheckRunner
from bist_signal_bot.release.readiness import ReleaseReadinessEvaluator
from bist_signal_bot.release.rehearsal import SafeLaunchRehearsalRunner
from bist_signal_bot.release.candidate import ReleaseCandidateBuilder
from bist_signal_bot.release.storage import ReleaseStore
from bist_signal_bot.release.notes import ReleaseNotesBuilder

def create_release_check_runner(settings: Settings | None = None) -> ReleaseCheckRunner:
    s = settings or get_settings()
    return ReleaseCheckRunner(settings=s)

def create_release_store(settings: Settings | None = None, base_dir: Path | None = None) -> ReleaseStore:
    s = settings or get_settings()
    return ReleaseStore(settings=s, base_dir=base_dir)

def create_release_readiness_evaluator(settings: Settings | None = None, base_dir: Path | None = None) -> ReleaseReadinessEvaluator:
    s = settings or get_settings()
    runner = create_release_check_runner(s)
    store = create_release_store(s, base_dir)
    return ReleaseReadinessEvaluator(
        check_runner=runner,
        storage=store,
        settings=s
    )

def create_safe_launch_rehearsal_runner(settings: Settings | None = None, base_dir: Path | None = None) -> SafeLaunchRehearsalRunner:
    s = settings or get_settings()
    return SafeLaunchRehearsalRunner(settings=s)

def create_release_candidate_builder(settings: Settings | None = None, base_dir: Path | None = None) -> ReleaseCandidateBuilder:
    s = settings or get_settings()
    readiness_eval = create_release_readiness_evaluator(s, base_dir)
    rehearsal = create_safe_launch_rehearsal_runner(s, base_dir)
    store = create_release_store(s, base_dir)
    notes = ReleaseNotesBuilder()

    return ReleaseCandidateBuilder(
        readiness_evaluator=readiness_eval,
        rehearsal_runner=rehearsal,
        notes_builder=notes,
        storage=store,
        settings=s
    )
