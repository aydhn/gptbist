from datetime import datetime, timezone
from types import SimpleNamespace

import numpy as np
import pandas as pd

from bist_signal_bot.core.audit import AuditEventType
from bist_signal_bot.model_loop.drift_monitor import (
    Adwin, DriftMonitor, ks_statistic_pvalue, psi)
from bist_signal_bot.model_loop.interface import TrainedModelInfo
from bist_signal_bot.model_loop.lifecycle import ModelLifecycle
from bist_signal_bot.model_loop.runtime_guard import drift_check_effective, ml_filter_effective
from bist_signal_bot.model_registry.models import ModelKind, ModelRecord, ModelRegistryStatus
from bist_signal_bot.model_registry.registry import LocalModelRegistry


class FakeStore:
    def __init__(self):
        self.d = {}

    def append_model(self, m):
        self.d[m.model_id] = m.model_copy(deep=True)

    def load_models(self, status=None):
        r = [m.model_copy(deep=True) for m in self.d.values()]
        return [m for m in r if status is None or m.status == status]

    def get_model(self, i):
        m = self.d.get(i)
        return m.model_copy(deep=True) if m else None


class Audit:
    def __init__(self):
        self.events = []

    def log_event(self, e):
        self.events.append(e)

    def types(self):
        return [e.event_type for e in self.events]


class Kill:
    def __init__(self, active=False):
        self.active = active

    def is_active(self, scope=None):
        return self.active


class Pre:
    def __init__(self, ok=True):
        self.ok = ok
        self.calls = 0

    def run_cli_preflight(self, name, payload=None):
        self.calls += 1
        return SimpleNamespace(passed=self.ok)


class Trainer:
    def __init__(self, verdict="CANDIDATE", sharpe=2.0):
        self.verdict, self.sharpe, self.n = verdict, sharpe, 0

    def train(self, as_of):
        self.n += 1
        return TrainedModelInfo(model_id=f"m{self.n}", kind="hgb", interval="1h", trained_through="2024-01-01",
                                n_events=100, oos_metrics={"net_sharpe": self.sharpe},
                                gate_verdict=self.verdict)

    def latest_oos_net_sharpe(self, model_id):
        return None


S = SimpleNamespace(MODEL_LOOP_MIN_DAYS_BETWEEN_RETRAIN=5, MODEL_LOOP_MIN_CHALLENGER_IMPROVEMENT=0.0,
                    RUNTIME_USE_ML_FILTER=False, RUNTIME_RUN_DRIFT_CHECK=False, MODEL_LOOP_AUTO_ENABLE_RUNTIME=False)


def rec(mid, status, sharpe=None, verdict="CANDIDATE", tags=(), kind=ModelKind.CLASSIFIER, meta=None):
    m = {"gate_verdict": verdict, "oos_metrics": {"net_sharpe": sharpe} if sharpe is not None else {}}
    m.update(meta or {})
    return ModelRecord(model_id=mid, model_name=mid, model_kind=kind, version="1",
                       created_at=datetime.now(timezone.utc), status=status, tags=list(tags), metadata=m)


def make(trainer=None, kill=None, pre=None, champion_sharpe=1.0):
    reg = LocalModelRegistry(None, FakeStore())
    if champion_sharpe is not None:
        reg.register_model(rec("champ", ModelRegistryStatus.ACTIVE_RESEARCH, champion_sharpe), confirm=True)
    audit = Audit()
    lc = ModelLifecycle(reg, trainer or Trainer(), DriftMonitor(S), audit, pre or Pre(), kill or Kill(), S)
    return lc, reg, audit


BAD_PERF = [1.0] * 200 + [0.0] * 200


# ------------------------------------------------------------------ stats
def test_psi_and_ks():
    rng = np.random.default_rng(0)
    a, b = rng.normal(size=2000), rng.normal(size=2000)
    assert psi(a, b) < 0.1
    assert psi(a, b + 1.5) > 0.25
    d, p = ks_statistic_pvalue(a, b)
    assert p > 0.01
    d2, p2 = ks_statistic_pvalue(a, b + 0.5)
    assert p2 < 1e-6 and d2 > d
    assert ks_statistic_pvalue(a, a)[1] == 1.0


def test_adwin_detects_shift_and_few_false_alarms():
    for seed in range(5):
        rng = np.random.default_rng(seed)
        ad = Adwin(delta=0.002)
        fa = sum(ad.add_element(float(x)) for x in rng.binomial(1, 0.5, 1500))
        assert fa <= 1
    rng = np.random.default_rng(1)
    ad = Adwin(delta=0.002)
    for x in rng.binomial(1, 0.7, 300):
        ad.add_element(float(x))
    delay = None
    for i, x in enumerate(rng.binomial(1, 0.2, 300)):
        if ad.add_element(float(x)):
            delay = i
            break
    assert delay is not None and delay < 100
    assert ad.last_change_direction == -1 and ad.width > 0


def test_drift_monitor_decisions():
    rng = np.random.default_rng(0)
    ref = pd.DataFrame({"a": rng.normal(size=500), "b": rng.normal(size=500)})
    same = pd.DataFrame({"a": rng.normal(size=500), "b": rng.normal(size=500)})
    shifted = pd.DataFrame({"a": rng.normal(size=500) + 3, "b": rng.normal(size=500) + 3})
    dm = DriftMonitor(S)
    assert not dm.check_features(ref, same).retrain
    d = dm.check_features(ref, shifted)
    assert d.retrain and d.severity == "alert"
    assert dm.check_performance(BAD_PERF).retrain
    assert not dm.check_performance([0.5, 0.4, 0.6] * 100).retrain
    assert not dm.check_performance([0.0] * 200 + [1.0] * 200).retrain  # improvement only


# -------------------------------------------------------------- lifecycle
def test_rejected_challenger_never_promoted():
    lc, reg, audit = make(Trainer("REJECTED", 5.0))
    rep = lc.evaluate("2024-03-01", perf_stream=BAD_PERF)
    assert rep.trained and not rep.promotion_recommended
    assert reg.get_model(rep.challenger_id).status == ModelRegistryStatus.FAILED_VALIDATION
    res = lc.promote(rep.challenger_id, confirm=True)
    assert res.status == "BLOCKED"
    assert lc.champion().model_id == "champ"
    assert AuditEventType.MODEL_LOOP_DRIFT_DETECTED in audit.types()
    assert AuditEventType.MODEL_LOOP_CHALLENGER_TRAINED in audit.types()
    assert AuditEventType.MODEL_LOOP_PROMOTED not in audit.types()


def test_candidate_promoted_only_with_confirm_via_preflight_and_audit():
    pre = Pre()
    lc, reg, audit = make(Trainer("CANDIDATE", 2.0), pre=pre)
    rep = lc.evaluate("2024-03-01", perf_stream=BAD_PERF)
    assert rep.promotion_recommended
    assert reg.get_model(rep.challenger_id).status == ModelRegistryStatus.CANDIDATE
    dry = lc.promote(rep.challenger_id)
    assert dry.status == "DRY_RUN" and dry.no_real_order_sent and "No real order sent." in dry.message
    assert lc.champion().model_id == "champ"
    res = lc.promote(rep.challenger_id, confirm=True)
    assert res.status == "PROMOTED" and pre.calls >= 1
    assert lc.champion().model_id == rep.challenger_id
    assert reg.get_model("champ").status == ModelRegistryStatus.ARCHIVED
    assert AuditEventType.MODEL_LOOP_PROMOTED in audit.types()
    ev = [e for e in audit.events if e.event_type == AuditEventType.MODEL_LOOP_PROMOTED][0]
    assert ev.metadata["no_real_order_sent"] is True
    # rollback
    assert lc.rollback().status == "DRY_RUN"
    rb = lc.rollback(confirm=True)
    assert rb.status == "PROMOTED" and lc.champion().model_id == "champ"
    assert AuditEventType.MODEL_LOOP_ROLLED_BACK in audit.types()


def test_worse_candidate_not_promotable():
    lc, reg, _ = make(Trainer("CANDIDATE", 0.5), champion_sharpe=1.0)
    rep = lc.evaluate("2024-03-01", perf_stream=BAD_PERF)
    assert not rep.promotion_recommended
    assert lc.promote(rep.challenger_id, confirm=True).status == "BLOCKED"


def test_kill_switch_blocks_promotion_and_training():
    lc, reg, audit = make(Trainer("CANDIDATE", 2.0))
    rep = lc.evaluate("2024-03-01", perf_stream=BAD_PERF)
    lc.kill_switch.active = True
    res = lc.promote(rep.challenger_id, confirm=True)
    assert res.status == "BLOCKED" and "kill switch active" in res.reasons
    assert lc.champion().model_id == "champ"
    rep2 = lc.evaluate("2024-06-01", perf_stream=BAD_PERF)
    assert not rep2.trained and rep2.skipped_reason == "kill_switch_active"


def test_preflight_failure_blocks_promotion():
    lc, reg, _ = make(Trainer("CANDIDATE", 2.0), pre=Pre(ok=False))
    rep = lc.evaluate("2024-03-01", perf_stream=BAD_PERF)
    assert lc.promote(rep.challenger_id, confirm=True).status == "BLOCKED"


def test_min_days_between_retrain():
    tr = Trainer("CANDIDATE", 2.0)
    lc, reg, _ = make(tr)
    assert lc.evaluate("2024-03-01", perf_stream=BAD_PERF).trained
    r2 = lc.evaluate("2024-03-03", perf_stream=BAD_PERF)
    assert not r2.trained and "min_days" in r2.skipped_reason and tr.n == 1
    assert lc.evaluate("2024-03-10", perf_stream=BAD_PERF).trained and tr.n == 2


def test_no_drift_no_training_and_no_champion_not_auto_promoted():
    tr = Trainer("CANDIDATE", 2.0)
    lc, reg, _ = make(tr, champion_sharpe=None)
    assert not lc.evaluate("2024-03-01", perf_stream=[0.5, 0.4, 0.6] * 100).trained
    rep = lc.evaluate("2024-03-01", perf_stream=BAD_PERF)
    assert rep.trained and not rep.promotion_recommended and lc.champion() is None


# ---------------------------------------------------------------- guard
def test_runtime_guard():
    reg = LocalModelRegistry(None, FakeStore())
    on = SimpleNamespace(RUNTIME_USE_ML_FILTER=True, RUNTIME_RUN_DRIFT_CHECK=True, MODEL_LOOP_AUTO_ENABLE_RUNTIME=True)
    ok, why = ml_filter_effective(on, reg)
    assert not ok and "no baseline" in why
    assert not drift_check_effective(on, reg)[0]
    reg.register_model(rec("b", ModelRegistryStatus.WATCH, kind=ModelKind.BASELINE), confirm=True)
    assert ml_filter_effective(on, reg)[0] and drift_check_effective(on, reg)[0]
    off = SimpleNamespace(RUNTIME_USE_ML_FILTER=False, RUNTIME_RUN_DRIFT_CHECK=False, MODEL_LOOP_AUTO_ENABLE_RUNTIME=False)
    assert not ml_filter_effective(off, reg)[0]
    auto = SimpleNamespace(RUNTIME_USE_ML_FILTER="auto", RUNTIME_RUN_DRIFT_CHECK=False, MODEL_LOOP_AUTO_ENABLE_RUNTIME=False)
    assert ml_filter_effective(auto, reg)[0]
    reg2 = LocalModelRegistry(None, FakeStore())
    assert not ml_filter_effective(auto, reg2)[0]
    reg2.register_model(rec("x", ModelRegistryStatus.FAILED_VALIDATION), confirm=True)
    assert not ml_filter_effective(on, reg2)[0]


import pytest


@pytest.mark.parametrize("verdict", ["WATCH", "INSUFFICIENT_DATA", "REJECTED", "", "candidate"])
@pytest.mark.parametrize("with_champion", [True, False])
def test_non_candidate_never_promoted_even_with_confirm_and_all_guards_ok(verdict, with_champion):
    """Gate-failing / non-CANDIDATE challenger ends non-champion (WATCH/FAILED_VALIDATION) and promote(confirm=True)
    is BLOCKED although preflight and kill switch are fine and its Sharpe is far better than the champion's."""
    pre = Pre(ok=True)
    lc, reg, audit = make(Trainer(verdict, 9.0), pre=pre, champion_sharpe=1.0 if with_champion else None)
    champ_before = lc.champion().model_id if with_champion else None
    rep = lc.evaluate("2024-03-01", perf_stream=BAD_PERF)
    assert rep.trained and not rep.promotion_recommended
    st = reg.get_model(rep.challenger_id).status
    assert st in (ModelRegistryStatus.WATCH, ModelRegistryStatus.FAILED_VALIDATION)
    for confirm in (False, True):
        res = lc.promote(rep.challenger_id, confirm=confirm)
        assert res.status == "BLOCKED"
        assert any("CANDIDATE required" in r for r in res.reasons)
    assert (lc.champion().model_id if with_champion else lc.champion()) == (champ_before if with_champion else None)
    assert reg.get_model(rep.challenger_id).status == st
    assert AuditEventType.MODEL_LOOP_PROMOTED not in audit.types()


def test_tampered_gate_verdict_metadata_still_needs_preflight_killswitch_and_confirm():
    """Even a genuine CANDIDATE is only promoted when preflight, kill switch AND confirm all hold."""
    lc, reg, audit = make(Trainer("CANDIDATE", 9.0), pre=Pre(ok=False))
    rep = lc.evaluate("2024-03-01", perf_stream=BAD_PERF)
    assert lc.promote(rep.challenger_id, confirm=True).status == "BLOCKED"
    lc.preflight.ok = True
    lc.kill_switch.active = True
    assert lc.promote(rep.challenger_id, confirm=True).status == "BLOCKED"
    lc.kill_switch.active = False
    assert lc.promote(rep.challenger_id, confirm=False).status == "DRY_RUN"
    assert lc.champion().model_id == "champ"
    assert AuditEventType.MODEL_LOOP_PROMOTED not in audit.types()


def test_ctx_as_of_accepts_tz_aware_datetime_without_warning():
    import warnings
    from bist_signal_bot.model_loop.daily_lifecycle import ctx_as_of

    class Ctx:
        index = pd.bdate_range("2024-01-01", periods=10)

        def truncate(self, n):
            return n

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert ctx_as_of(Ctx(), pd.Timestamp("2024-01-05", tz="UTC").to_pydatetime()) == 5
