import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.edge_validation.cv import (
    CombinatorialPurgedCV, PurgedKFold, assert_no_leakage, purged_walk_forward)

TZ = "Europe/Istanbul"


def events(n=120, span_h=5, step_h=1):
    t0 = pd.date_range("2024-01-01", periods=n, freq=f"{step_h}h", tz=TZ)
    return pd.Series(t0), pd.Series(t0 + pd.Timedelta(hours=span_h))


def naive_kfold(n, k):
    for f in np.array_split(np.arange(n), k):
        yield np.setdiff1d(np.arange(n), f), f


def test_purged_kfold_no_leakage_and_naive_leaks():
    t0, t1 = events()
    leaks = 0
    for tr, te in naive_kfold(len(t0), 5):
        try:
            assert_no_leakage(tr, te, t0, t1)
        except AssertionError:
            leaks += 1
    assert leaks == 5  # every naive fold leaks (labels straddle the fold edges)
    folds = list(PurgedKFold(5).split(t0, t1))
    assert len(folds) == 5
    for tr, te in folds:
        assert_no_leakage(tr, te, t0, t1)
        assert len(set(tr) & set(te)) == 0
    # every sample is tested exactly once
    assert sorted(np.concatenate([te for _, te in folds])) == list(range(len(t0)))
    # purge removed the overlapping events before the middle fold
    assert len(folds[2][0]) < len(t0) - len(folds[2][1])


def test_embargo_effect():
    t0, t1 = events()
    base = list(PurgedKFold(5).split(t0, t1))
    emb = list(PurgedKFold(5, embargo_bars=6).split(t0, t1))
    for (b_tr, te), (e_tr, te2) in zip(base, emb):
        assert np.array_equal(te, te2)
        assert set(e_tr) <= set(b_tr)
    tr, te = base[1]
    removed = sorted(set(tr) - set(emb[1][0]))
    end = t1.iloc[te].max()
    assert removed and all(end < t0.iloc[i] <= end + pd.Timedelta(hours=6) for i in removed)
    pct = list(PurgedKFold(5, embargo_pct=0.05).split(t0, t1))
    assert len(pct[1][0]) < len(base[1][0])
    td = list(PurgedKFold(5, embargo=pd.Timedelta(hours=6)).split(t0, t1))
    removed_td = sorted(set(base[1][0]) - set(td[1][0]))
    assert removed_td and all(end < t0.iloc[i] <= end + pd.Timedelta(hours=6) for i in removed_td)
    assert_no_leakage(td[1][0], td[1][1], t0, t1, embargo=pd.Timedelta(hours=6))
    with pytest.raises(AssertionError):
        assert_no_leakage(base[1][0], base[1][1], t0, t1, embargo=pd.Timedelta(hours=6))


def test_cpcv_counts_and_paths():
    t0, t1 = events(n=180)
    cv = CombinatorialPurgedCV(6, 2, embargo_bars=2)
    assert cv.n_splits == 15 and cv.n_paths == 5
    splits = list(cv.split(t0, t1))
    assert len(splits) == 15
    for tr, te, combo in splits:
        assert len(combo) == 2
        assert_no_leakage(tr, te, t0, t1)
    # every sample is in a test set exactly 5 times (once per path)
    cnt = np.zeros(len(t0), int)
    for _, te, _ in splits:
        cnt[te] += 1
    assert (cnt == 5).all()
    preds = [{g: f"s{si}g{g}" for g in combo} for si, (_, _, combo) in enumerate(splits)]
    paths = cv.assemble_paths(preds)
    assert len(paths) == 5
    for p in paths:
        assert sorted(p) == list(range(6))  # each group exactly once per path
    used = [(si, g) for pm in cv.path_map() for si, g in pm]
    assert len(set(used)) == 30  # each (split, group) test slot used exactly once
    assert CombinatorialPurgedCV(5, 2).n_paths == 4


def test_walk_forward_no_train_label_after_test_start():
    t0, t1 = events(n=24 * 40, span_h=30)
    for expanding in (False, True):
        wins = list(purged_walk_forward(t0, t1, train_span=10, test_span=5, step=5,
                                        embargo=1, expanding=expanding))
        assert len(wins) >= 4
        for tr, te in wins:
            assert t1.iloc[tr].max() < t0.iloc[te].min() - pd.Timedelta(days=1)
            assert_no_leakage(tr, te, t0, t1, embargo=pd.Timedelta(days=1))
    r = list(purged_walk_forward(t0, t1, 10, 5, 5))
    x = list(purged_walk_forward(t0, t1, 10, 5, 5, expanding=True))
    assert len(x[-1][0]) > len(r[-1][0])


def test_panel_multi_symbol_purge_by_time():
    t0a, t1a = events(n=60)
    t0 = pd.concat([t0a, t0a], ignore_index=True)
    t1 = pd.concat([t1a, t1a], ignore_index=True)
    symbol = np.array(["AAA"] * 60 + ["BBB"] * 60)
    # test made only of AAA events: naive train still holds overlapping BBB events
    te = np.arange(20, 30)
    tr = np.setdiff1d(np.arange(120), te)
    with pytest.raises(AssertionError):
        assert_no_leakage(tr, te, t0, t1)
    for tr, te in PurgedKFold(4).split(t0, t1):
        assert_no_leakage(tr, te, t0, t1)
        lo, hi = t0.iloc[te].min(), t1.iloc[te].max()
        assert not ((t0.iloc[tr] <= hi) & (t1.iloc[tr] >= lo)).any()
        assert set(symbol[tr]) == {"AAA", "BBB"}
