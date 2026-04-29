import pytest
from bist_signal_bot.app.healthcheck import run_healthcheck

def test_healthcheck_universe_fields():
    hc = run_healthcheck()
    assert "symbol_universe" in hc
    univ = hc["symbol_universe"]

    expected_fields = [
        "universe_dir",
        "universe_file_path",
        "universe_file_exists",
        "auto_initialize_universe",
        "auto_snapshot_universe",
        "watchlists_dir",
        "snapshots_dir",
        "default_seed_count",
        "local_universe_symbol_count",
        "active_symbol_count",
        "inactive_symbol_count",
        "validation_passed",
        "issue_count"
    ]

    for field in expected_fields:
        assert field in univ

    assert isinstance(univ["universe_file_exists"], bool)
    assert isinstance(univ["validation_passed"], bool)
    assert univ["default_seed_count"] > 0
