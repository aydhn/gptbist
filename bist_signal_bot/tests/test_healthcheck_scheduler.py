def test_healthcheck_imports():
    from bist_signal_bot.scheduler.models import ScheduledJobType
    assert ScheduledJobType.HEALTHCHECK.value == "HEALTHCHECK"
