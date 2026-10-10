"""Heartbeat storage, STALE_HEARTBEAT alert and fail-closed paths (kill switch / fetch / chain). Offline, tmp dirs only.
No real order is ever sent."""
import json
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from bist_signal_bot.forward import health as H
from bist_signal_bot.forward import shadow as S
from bist_signal_bot.forward.chain import HashChain
from bist_signal_bot.monitoring.heartbeat import HeartbeatManager
from bist_signal_bot.monitoring.models import HealthLevel, HeartbeatRecord, MonitoringComponent
from bist_signal_bot.monitoring.storage import HeartbeatFileStore, MonitoringStore
from bist_signal_bot.tests.test_forward_shadow import D1, D2, env, now_of  # noqa: F401  (fixture reuse)


def _rec(ts, comp=MonitoringComponent.RUNTIME, st=HealthLevel.HEALTHY, msg="m"):
    return HeartbeatRecord(heartbeat_id=f"id{ts.timestamp()}", timestamp=ts, component=comp, status=st, message=msg)


def test_store_append_load_newest_first_and_corrupt_line_skipped(tmp_path):
    fs = HeartbeatFileStore(tmp_path / "hb.jsonl")
    assert fs.load_recent_heartbeats() == [] and fs.last_heartbeat() is None and fs.is_stale(60)
    t0 = datetime.utcnow()
    for i in range(3):
        fs.append_heartbeat(_rec(t0 + timedelta(seconds=i), msg=f"m{i}"))
    with open(fs.path, "a", encoding="utf-8") as f:
        f.write('{"heartbeat_id": "partial')  # crash-truncated tail
    got = fs.load_recent_heartbeats()
    assert [r.message for r in got] == ["m2", "m1", "m0"]
    assert len(fs.load_recent_heartbeats(limit=2)) == 2


def test_stale_detection_configurable_and_manager_wiring(tmp_path, settings_factory):
    st = settings_factory(MONITORING_HEARTBEAT_MAX_AGE_SECONDS=60)
    store = MonitoringStore(tmp_path)
    hm = HeartbeatManager(store, st)
    assert hm.check_stale(MonitoringComponent.RUNTIME)["reason"] == "no_heartbeat"  # fail closed
    hm.record(MonitoringComponent.RUNTIME, HealthLevel.HEALTHY, "ok")
    assert (tmp_path / "heartbeats.jsonl").exists()
    assert hm.latest(MonitoringComponent.RUNTIME).message == "ok"
    assert hm.latest(MonitoringComponent.DATA) is None
    assert hm.check_stale(MonitoringComponent.RUNTIME)["stale"] is False
    hm2 = HeartbeatManager(MonitoringStore(tmp_path / "other"), st)
    hm2.storage.append_heartbeat(_rec(datetime.utcnow() - timedelta(seconds=600)))
    assert hm2.check_stale(MonitoringComponent.RUNTIME)["stale"] is True  # 600s > 60s configured
    assert hm2.check_stale(MonitoringComponent.RUNTIME, max_age_seconds=10_000)["stale"] is False
    assert hm2.component_health_from_heartbeat(MonitoringComponent.RUNTIME, 60) == HealthLevel.DEGRADED
    assert MonitoringStore(st).base_dir.name == "monitoring"  # Settings accepted (CLI passes settings)


def test_forward_emits_start_and_ok_beats_with_reasons(env):  # noqa: F811
    st, cfg, arch, _ = env
    S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    beats = H.ForwardHeartbeatStore(cfg.heartbeat_path).load_recent_heartbeats()
    assert [b.metadata["phase"] for b in beats[:2]] == ["ok", "start"]
    S.run_daily(cfg, now=now_of(D2), fetch=False, archive=arch)  # archive ends D1 -> STALE
    b = H.ForwardHeartbeatStore(cfg.heartbeat_path).load_recent_heartbeats()[0]
    assert b.metadata["phase"] == "fail" and any("freshness_gate=STALE" in r for r in b.metadata["reasons"])


def test_stale_heartbeat_alert_in_health_and_dedupe(env):  # noqa: F811
    st, cfg, arch, _ = env
    S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    assert H.heartbeat_alerts(cfg) == []
    h = H.build_health(cfg, now=now_of(D1), archive=arch)
    assert h["overall"] == "OK" and not h["heartbeat_stale"]
    future = datetime.utcnow() + timedelta(minutes=cfg.i("FORWARD_HEARTBEAT_MAX_AGE_MINUTES", 4500) + 5)
    al = H.heartbeat_alerts(cfg, now=future)
    assert al and al[0]["kind"] == "STALE_HEARTBEAT" and al[0]["severity"] == "HIGH"
    assert {"key", "title", "message"} <= set(al[0])
    assert len(H.emit_alerts(cfg, al)) == 1 and H.emit_alerts(cfg, al) == []
    old = [json.loads(x) for x in cfg.heartbeat_path.read_text().splitlines()]
    for o in old:
        o["timestamp"] = (datetime.utcnow() - timedelta(days=30)).isoformat()
    cfg.heartbeat_path.write_text("\n".join(json.dumps(o) for o in old) + "\n")
    h2 = H.build_health(cfg, now=now_of(D1), archive=arch)
    assert h2["heartbeat_stale"] and h2["overall"] == "ATTENTION" and "STALE_HEARTBEAT" in h2["alerts_new"]


# ---------------- fail-closed: forward shadow ----------------
def _decisions(cfg):
    return [r for r in HashChain(cfg.decisions_path).records() if r.get("type") == "decision"]


def test_corrupt_chain_means_no_decision_and_alert(env):  # noqa: F811
    st, cfg, arch, _ = env
    S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    cfg.decisions_path.write_text(cfg.decisions_path.read_text().replace('"rank":1', '"rank":7'))
    size = cfg.decisions_path.stat().st_size
    r = S.run_daily(cfg, now=now_of(D2), fetch=False, archive=arch)
    assert r["status"] == "FAILED" and r["decisions_written"] == 0 and "HASH_CHAIN_BREAK" in r["alerts_new"]
    assert cfg.decisions_path.stat().st_size == size  # nothing appended
    assert H.ForwardHeartbeatStore(cfg.heartbeat_path).load_recent_heartbeats()[0].metadata["phase"] == "fail"


def test_kill_switch_lookup_error_fails_closed(env, monkeypatch):  # noqa: F811
    st, cfg, arch, _ = env

    def boom(_cfg):
        raise OSError("kill switch file unreadable")
    monkeypatch.setattr(S, "kill_switch_state", boom)
    r = S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    assert r["status"] == "FAILED" and r["decisions_written"] == 0 and "JOB_FAILURE" in r["alerts_new"]
    assert _decisions(cfg) == []


def test_corrupt_kill_switch_file_blocks_entries(env):  # noqa: F811
    st, cfg, arch, _ = env
    from bist_signal_bot.security.kill_switch import KillSwitchManager
    km = KillSwitchManager(st, cfg.data_dir)
    km.file_path.parent.mkdir(parents=True, exist_ok=True)
    km.file_path.write_text("{not json")
    r = S.run_daily(cfg, now=now_of(D1), fetch=False, archive=arch)
    assert r["decisions_written"] == 0 and r["status"] in ("KILL_SWITCH", "FAILED")


def test_fetch_error_on_stale_archive_means_stale_no_decisions(env):  # noqa: F811
    st, cfg, arch, _ = env

    def bad_fetch(*a, **k):
        raise ConnectionError("network down")
    r = S.run_daily(cfg, now=now_of(D2), fetch=True, fetch_fn=bad_fetch, archive=arch)
    assert r["status"] == "STALE" and r["decisions_written"] == 0
    assert "STALE_DATA" in r["alerts_new"] and _decisions(cfg) == []


def test_refresh_archive_raising_is_recorded_not_silent(env, monkeypatch):  # noqa: F811
    st, cfg, arch, _ = env

    def boom(*a, **k):
        raise RuntimeError("boom")
    monkeypatch.setattr(S, "refresh_archive", boom)
    r = S.run_daily(cfg, now=now_of(D2), fetch=True, archive=arch)
    assert "fetch: boom" in r["errors"] and r["decisions_written"] == 0 and r["status"] == "STALE"


# ---------------- fail-closed: runtime orchestrator paper entry ----------------
class _Paper:
    def __init__(self):
        self.calls = 0

    def run(self, *a, **k):
        self.calls += 1
        return {"status": "OK"}


def _orch(settings, ks, paper):
    from bist_signal_bot.runtime.orchestrator import RuntimeOrchestrator
    return RuntimeOrchestrator(kill_switch=ks, paper_engine=paper, settings=settings)


def _cfg():
    return SimpleNamespace(use_paper=True, dry_run=False, strategy_name="", symbols=[], metadata={}, source=None,
                           timeframe=None)


@pytest.mark.parametrize("mode", ["active", "lookup_error"])
def test_orchestrator_blocks_paper_when_kill_switch_active_or_unreadable(settings_factory, tmp_data_dir, mode):
    from bist_signal_bot.security.kill_switch import KillSwitchManager
    from bist_signal_bot.security.models import KillSwitchScope
    st = settings_factory()
    ks = KillSwitchManager(st, tmp_data_dir)
    if mode == "active":
        ks.activate([KillSwitchScope.PAPER], "test")
    else:
        def unreadable(*a, **k):
            raise OSError("unreadable")
        ks.is_active = unreadable
    paper = _Paper()
    o = _orch(st, ks, paper)
    res = SimpleNamespace(metadata={}, job_results=[], paper_result_summary=None)
    o._execute_paper_run(_cfg(), res)
    assert paper.calls == 0
    assert res.metadata["alerts"][0]["kind"] == "PAPER_BLOCKED" and res.metadata["skipped_steps"]


def test_orchestrator_paper_runs_when_kill_switch_off_and_surfaces_engine_error(settings_factory, tmp_data_dir):
    from bist_signal_bot.security.kill_switch import KillSwitchManager
    st = settings_factory()
    paper = _Paper()
    o = _orch(st, KillSwitchManager(st, tmp_data_dir), paper)
    res = SimpleNamespace(metadata={}, job_results=[], paper_result_summary=None)
    o._execute_paper_run(_cfg(), res)
    assert paper.calls == 1 and "alerts" not in res.metadata
    paper.run = lambda *a, **k: {"status": "ERROR", "error": "Kill Switch Active"}
    res2 = SimpleNamespace(metadata={}, job_results=[], paper_result_summary=None)
    o._execute_paper_run(_cfg(), res2)
    assert res2.metadata["alerts"][0]["kind"] == "PAPER_ERROR"


def test_orchestrator_heartbeats_start_and_finish(settings_factory, tmp_data_dir):
    from bist_signal_bot.runtime.models import RuntimePipelineStatus
    from bist_signal_bot.security.kill_switch import KillSwitchManager
    st = settings_factory(MONITORING_HEARTBEAT_ENABLED=True)
    o = _orch(st, KillSwitchManager(st, tmp_data_dir), _Paper())
    cfg = o.build_default_pipeline_config()
    cfg.dry_run, cfg.save_reports = True, False
    res = o.run_once(cfg)
    beats = MonitoringStore(st).load_recent_heartbeats()
    phases = [b.metadata.get("phase") for b in beats]
    assert "start" in phases and phases[0] in ("ok", "fail"), (res.status, phases)
    assert beats[0].runtime_run_id == res.run_id
    good = res.status in (RuntimePipelineStatus.SUCCESS, RuntimePipelineStatus.SKIPPED)
    assert beats[0].metadata["phase"] == ("ok" if good else "fail")
