from bist_signal_bot.core.audit import AuditEventType  # noqa: F401
from bist_signal_bot.model_loop.daily_cycle import run_daily_cycle
from bist_signal_bot.model_loop.drift_monitor import DriftMonitor
from bist_signal_bot.model_loop.lifecycle import ModelLifecycle
from bist_signal_bot.model_registry.models import ModelRegistryStatus
from bist_signal_bot.model_registry.registry import LocalModelRegistry
from bist_signal_bot.tests.test_model_loop_lifecycle import Audit, FakeStore, Kill, Pre, S, Trainer, rec


def mk(verdict="CANDIDATE", sharpe=2.0, kill=False, champion=True):
    reg = LocalModelRegistry(None, FakeStore())
    if champion:
        reg.register_model(rec("champ", ModelRegistryStatus.ACTIVE_RESEARCH, 1.0), confirm=True)
    lc = ModelLifecycle(reg, Trainer(verdict, sharpe), DriftMonitor(S), Audit(), Pre(), Kill(kill), S)
    return reg, lc


def snapshot(reg):
    return sorted((m.model_id, m.status.value) for m in reg.list_models())


def test_not_due_is_noop():
    reg, lc = mk()
    r = rec("d1", ModelRegistryStatus.WATCH, tags=("daily",), meta={"loop_as_of": "2026-01-08T00:00:00+00:00"})
    r.owner_module = "model_loop"
    reg.register_model(r, confirm=True)
    before = snapshot(reg)
    res = run_daily_cycle(reg, lc, "2026-01-10", only_if_due=True, confirm=True)
    assert res["status"] == "NOOP_NOT_DUE" and snapshot(reg) == before and lc.trainer.n == 0
    assert all(l.endswith("No real order sent.") for l in res["lines"])


def test_dry_run_changes_no_state():
    reg, lc = mk()
    before = snapshot(reg)
    res = run_daily_cycle(reg, lc, "2026-01-10", dry_run=True, confirm=True)
    assert res["status"] == "DRY_RUN" and snapshot(reg) == before and lc.trainer.n == 0


def test_non_candidate_never_promoted_even_with_confirm():
    reg, lc = mk(verdict="REJECTED")
    res = run_daily_cycle(reg, lc, "2026-01-10", confirm=True)
    assert res["status"] == "REPORT_ONLY" and res["promotion"] is None
    assert lc.champion().model_id == "champ"


def test_candidate_without_confirm_is_dry_run_and_with_confirm_promotes():
    reg, lc = mk()
    res = run_daily_cycle(reg, lc, "2026-01-10")
    assert res["status"] == "DRY_RUN" and lc.champion().model_id == "champ"
    reg2, lc2 = mk()
    res2 = run_daily_cycle(reg2, lc2, "2026-01-10", confirm=True)
    assert res2["status"] == "PROMOTED" and lc2.champion().model_id == "m1"


def test_kill_switch_blocks_cycle_promotion_and_rollback():
    reg, lc = mk(kill=True)
    res = run_daily_cycle(reg, lc, "2026-01-10", confirm=True)
    assert res["status"] == "NO_CHALLENGER" and lc.champion().model_id == "champ"
    reg2, lc2 = mk()
    run_daily_cycle(reg2, lc2, "2026-01-10", confirm=True)
    assert lc2.champion().model_id == "m1"
    lc2.kill_switch = Kill(True)
    assert lc2.promote("m1", confirm=True).status == "BLOCKED"
    rb = lc2.rollback(confirm=True)
    assert rb.status == "BLOCKED" and "kill switch active" in rb.reasons and lc2.champion().model_id == "m1"
    lc2.kill_switch = Kill(False)
    assert lc2.rollback(confirm=True).status == "PROMOTED" and lc2.champion().model_id == "champ"


def test_cli_parser_daily_cycle():
    from bist_signal_bot.cli.model_loop_cli import build_parser
    a = build_parser().parse_args(["daily-cycle", "--only-if-due", "--dry-run"])
    assert a.only_if_due and a.dry_run and not a.confirm and a.retrain_days == 7


def test_mode_labels():
    reg, lc = mk()
    assert run_daily_cycle(reg, lc, "2026-01-10", dry_run=True)["mode"] == "DRY_RUN"
    reg, lc = mk()
    res = run_daily_cycle(reg, lc, "2026-01-10")
    assert res["mode"] == "TRAIN_NO_PROMOTE" and any("challenger kaydedildi; terfi yok" in l for l in res["lines"])
    reg, lc = mk()
    assert run_daily_cycle(reg, lc, "2026-01-10", confirm=True)["mode"] == "CONFIRM"


def test_cli_due_check_and_training_share_as_of():
    from types import SimpleNamespace
    import pandas as pd
    from bist_signal_bot.cli.model_loop_cli import _cycle_as_of
    ctx = SimpleNamespace(index=pd.DatetimeIndex(["2026-01-01", "2026-01-08"]))
    a, c = _cycle_as_of(SimpleNamespace(as_of=None), lambda: ctx)
    assert a == ctx.index[-1] and c is ctx
    a, c = _cycle_as_of(SimpleNamespace(as_of="2026-02-01"), lambda: 1 / 0)
    assert a == "2026-02-01" and c is None
