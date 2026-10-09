"""Model-loop tests: offline, seeded synthetic archive in tmp. No network, no orders."""
import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.edge_validation.ledger import TrialLedger
from bist_signal_bot.intraday.archive import BarArchive
from bist_signal_bot.model_loop import features as F
from bist_signal_bot.model_loop import training as T
from bist_signal_bot.model_loop.interface import TrainedModelInfo, TrainerProtocol
from bist_signal_bot.model_registry.models import ModelRegistryStatus

SYMS = ["AAA", "BBB", "CCC", "DDD", "EEE"]


def make_bars(seed, days=160, phi=0.0, sigma=0.004):
    """Random-walk 1h bars (7/day); phi>0 adds bar-to-bar momentum (a learnable signal)."""
    rng = np.random.default_rng(seed)
    day_idx = pd.bdate_range("2024-01-02", periods=days)
    ts = [d + pd.Timedelta(hours=h) for d in day_idx for h in range(10, 17)]
    n = len(ts)
    noise = rng.normal(0, sigma, n)
    r = np.zeros(n)
    for i in range(n):
        r[i] = noise[i] + (phi * r[i - 1] if i else 0.0)
    c = 50.0 * np.exp(np.cumsum(r))
    o = np.concatenate([[50.0], c[:-1]])
    h = np.maximum(o, c) * (1 + np.abs(rng.normal(0, 0.0005, n)))
    l = np.minimum(o, c) * (1 - np.abs(rng.normal(0, 0.0005, n)))
    vol = rng.uniform(0.8, 1.2, n) * 1_000_000
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c, "volume": vol},
                        index=pd.DatetimeIndex(ts, tz="Europe/Istanbul"))


def fill(path, seed, phi=0.0, days=160):
    a = BarArchive(path=path)
    for k, s in enumerate(SYMS):
        a.upsert_bars(make_bars(seed * 100 + k, days, phi), s, "1h", "test")
    return a


def test_features_are_causal():
    bars = make_bars(1, days=40)
    full = F.build_features(bars, "1h")
    cut = 150
    part = F.build_features(bars.iloc[:cut], "1h")
    pd.testing.assert_frame_equal(full.iloc[:cut], part, check_exact=False, rtol=1e-7, atol=1e-9)
    # mutate the future: past features must not change
    b2 = bars.copy()
    b2.iloc[cut:, :4] *= 1.37
    b2.iloc[cut:, 4] *= 5
    pd.testing.assert_frame_equal(full.iloc[:cut], F.build_features(b2, "1h").iloc[:cut],
                                  check_exact=False, rtol=1e-7, atol=1e-9)


def test_panel_shape_and_session_bound(tmp_path):
    a = fill(tmp_path / "b.sqlite", 1, days=60)
    try:
        p = F.build_panel(a, SYMS, "1h", None, None, horizon_bars=4)
    finally:
        a.close()
    assert len(p) > 1000
    assert not p[F.FEATURE_COLUMNS].isna().any().any()
    assert (p["t1"] >= p["t0"]).all()
    d0 = p["t0"].dt.tz_convert("Europe/Istanbul").dt.normalize()
    d1 = p["t1"].dt.tz_convert("Europe/Istanbul").dt.normalize()
    assert (d0 == d1).all()  # no overnight carry
    assert set(p["symbol"]) == set(SYMS)


def test_panel_respects_as_of(tmp_path):
    a = fill(tmp_path / "b.sqlite", 1, days=60)
    try:
        p = F.build_panel(a, SYMS, "1h", None, "2024-02-15", horizon_bars=4)
    finally:
        a.close()
    assert p["t1"].max() < pd.Timestamp("2024-02-16", tz="Europe/Istanbul")


def _train(tmp_path, settings_factory, seed, phi, tag, kind="hgb", days=160):
    st = settings_factory()
    a = fill(tmp_path / f"b_{tag}.sqlite", seed, phi, days)
    led = TrialLedger(path=tmp_path / f"led_{tag}.sqlite")
    reg = T.make_registry(st)
    try:
        info = T.train_model(a, SYMS, "1h", "2025-12-31", st, model_kind=kind, registry=reg, ledger=led,
                             min_train_events=1000, seed=7)
    finally:
        a.close()
    return info, reg, led, st


def test_noise_registered_with_warning_not_candidate(tmp_path, settings_factory):
    info, reg, led, _ = _train(tmp_path, settings_factory, 3, 0.0, "n")
    assert isinstance(info, TrainedModelInfo)
    assert abs(info.oos_metrics["auc"] - 0.5) < 0.05
    assert info.gate_verdict != "CANDIDATE"
    rec = reg.get_model(info.model_id)
    assert rec is not None and rec.status == ModelRegistryStatus.WATCH
    assert any("no proven edge" in w for w in rec.warnings)
    assert led.n_trials("ml_hgb") >= 3  # every threshold trial recorded


def test_planted_signal_has_auc_and_registry_artifact(tmp_path, settings_factory):
    info, reg, _, st = _train(tmp_path, settings_factory, 4, 0.6, "s", kind="logreg")
    assert info.oos_metrics["auc"] > 0.55
    rec = reg.get_model(info.model_id)
    assert rec.model_card_id and rec.artifact_id
    cards = reg.store.load_model_cards(info.model_id)
    assert len(cards) == 1 and "CandidateGate verdict" in cards[0].validation_summary
    assert rec.status in (ModelRegistryStatus.CANDIDATE, ModelRegistryStatus.WATCH)
    assert rec.status != ModelRegistryStatus.ACTIVE_RESEARCH  # never auto-promoted
    assert all(m.status != ModelRegistryStatus.ACTIVE_RESEARCH for m in reg.list_models())
    assert T.latest_oos_net_sharpe(info.model_id, reg) == rec.metadata["oos_net_sharpe_annual"]
    # artifact loads and predicts causally on the latest bar
    bars = {s: make_bars(40 + k, 160, 0.6) for k, s in enumerate(SYMS)}
    pr = T.predict_proba(info.model_id, bars, reg)
    assert set(pr) == set(SYMS) and all(0 <= v <= 1 for v in pr.values())
    cut = {s: b.iloc[:-5] for s, b in bars.items()}
    full_prev = T.predict_proba(info.model_id, cut, reg)
    mutated = {s: pd.concat([b.iloc[:-5], b.iloc[-5:] * 1.5]) for s, b in bars.items()}
    assert T.predict_proba(info.model_id, {s: m.iloc[:-5] for s, m in mutated.items()}, reg) == full_prev


def test_cpcv_splits_all_leak_checked_and_deterministic(tmp_path, settings_factory, monkeypatch):
    calls = []
    real = T.assert_no_leakage
    monkeypatch.setattr(T, "assert_no_leakage", lambda *a, **k: (calls.append(1), real(*a, **k))[1])
    i1, *_ = _train(tmp_path, settings_factory, 5, 0.0, "d1", days=100)
    assert len(calls) == 15 == i1.oos_metrics["cpcv_splits_checked"]
    (tmp_path / "x").mkdir()
    i2, *_ = _train(tmp_path, settings_factory, 5, 0.0, "d2", days=100)
    for k in ("auc", "brier", "log_loss", "calibration_error"):
        assert i1.oos_metrics[k] == pytest.approx(i2.oos_metrics[k], abs=1e-12)


def test_insufficient_events_raises(tmp_path, settings_factory):
    st = settings_factory()
    a = fill(tmp_path / "b.sqlite", 1, days=20)
    try:
        with pytest.raises(ValueError):
            T.train_model(a, SYMS, "1h", "2025-12-31", st, registry=T.make_registry(st),
                          ledger=TrialLedger(path=tmp_path / "l.sqlite"))
    finally:
        a.close()


def test_trainer_protocol():
    assert issubclass(T.IntradayModelTrainer, TrainerProtocol) or isinstance(
        T.IntradayModelTrainer(None, [], "1h"), TrainerProtocol)


def test_cli_parser():
    from bist_signal_bot.cli.model_loop_cli import build_parser
    a = build_parser().parse_args(["train", "--interval", "1h", "--all-archived", "--kind", "logreg"])
    assert a.kind == "logreg" and a.all_archived
