"""Shared pytest fixtures: deterministic seed, temp data dir, Settings factory."""

import random

import numpy as np
import pytest

from bist_signal_bot.config.settings import Settings


@pytest.fixture(autouse=True)
def _seed_everything():
    random.seed(1234)
    np.random.seed(1234)
    yield


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Empty data directory under pytest's tmp_path (never touches ./data)."""
    d = tmp_path / "data"
    d.mkdir()
    return d


@pytest.fixture
def settings_factory(tmp_data_dir):
    """Build a Settings pointing DATA_DIR at tmp_data_dir, with optional overrides."""

    def make(**overrides):
        return Settings(DATA_DIR=str(tmp_data_dir), **overrides)

    return make


@pytest.fixture(autouse=True)
def _global_pool_small_universe_ok():
    """Test panels are small; production default GLOBAL_POOL_MIN_UNIVERSE=100 would exclude them from the global-DSR
    pool. Tests that exercise the filter pass min_universe / set the attribute explicitly."""
    from bist_signal_bot.config.settings import get_settings
    s = get_settings()
    old = getattr(s, "GLOBAL_POOL_MIN_UNIVERSE", 100)
    s.GLOBAL_POOL_MIN_UNIVERSE = 0
    yield
    s.GLOBAL_POOL_MIN_UNIVERSE = old
