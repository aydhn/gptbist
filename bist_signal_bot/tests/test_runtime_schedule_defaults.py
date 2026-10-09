from bist_signal_bot.app.runtime_app import create_runtime_schedule_config_from_settings
from bist_signal_bot.config.settings import get_settings


def test_schedule_config_has_typed_bools():
    cfg = create_runtime_schedule_config_from_settings(get_settings())
    assert isinstance(cfg.run_immediately, bool)
    assert isinstance(cfg.stop_on_failure, bool)
