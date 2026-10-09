from bist_signal_bot.config.defaults import DEFAULTS
from bist_signal_bot.config.settings import Settings, _default_for


def test_unknown_dir_name_key_never_equals_its_own_name():
    assert _default_for("FOO_BAR_DIR_NAME") == "foo_bar"
    assert Settings().UNKNOWN_THING_DIR_NAME == "unknown_thing"


def test_storage_dir_names_are_real_folder_names():
    s = Settings()
    assert s.MARKET_DATA_DIR_NAME == "market_data"
    assert s.OPTIMIZATION_RESULTS_DIR_NAME == "optimization"
    assert s.DATA_PROVIDER_HEALTH_DIR_NAME == "provider_health"
    for key, value in DEFAULTS.items():
        if key.endswith("_DIR_NAME"):
            assert not value.endswith("_dir_name"), key


def test_inline_getattr_defaults_are_promoted_to_defaults():
    s = Settings()
    assert s.BACKTEST_MIN_TRADES_WARNING == 5
    assert s.DATA_YFINANCE_SUFFIX == ".IS"
