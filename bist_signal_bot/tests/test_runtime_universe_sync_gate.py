from types import SimpleNamespace

import pytest

from bist_signal_bot.config.defaults import DEFAULTS
from bist_signal_bot.runtime.orchestrator import RuntimeOrchestrator


def _orch(settings):
    o = RuntimeOrchestrator.__new__(RuntimeOrchestrator)
    o.settings = settings
    o.scanner_engine = None
    return o


@pytest.fixture
def calls(monkeypatch):
    seen = []
    import bist_signal_bot.data.universe_sync as us

    monkeypatch.setattr(us, "sync_if_stale", lambda s, *a, **k: seen.append(s))
    return seen


def _run(o, dry_run=False):
    o._execute_data_refresh(SimpleNamespace(dry_run=dry_run), SimpleNamespace(job_results=[]), {})


def test_default_is_false_and_runtime_never_syncs(calls):
    assert DEFAULTS["RUNTIME_UNIVERSE_AUTO_SYNC"] is False
    # INTRADAY auto-sync on must NOT make runtime sync
    _run(_orch(SimpleNamespace(INTRADAY_UNIVERSE_AUTO_SYNC=True)))
    _run(_orch(SimpleNamespace(INTRADAY_UNIVERSE_AUTO_SYNC=True, RUNTIME_UNIVERSE_AUTO_SYNC=False)))
    assert calls == []


def test_runtime_sync_only_when_explicitly_enabled(calls):
    _run(_orch(SimpleNamespace(RUNTIME_UNIVERSE_AUTO_SYNC=True)))
    assert len(calls) == 1
    _run(_orch(SimpleNamespace(RUNTIME_UNIVERSE_AUTO_SYNC=True)), dry_run=True)
    assert len(calls) == 1


def test_intraday_default_autosync_preserved():
    assert DEFAULTS["INTRADAY_UNIVERSE_AUTO_SYNC"] is True
