"""H2a: label purge/embargo end uses the REALIZED (deferred) exit row, not the nominal t1 = pos + horizon."""
import numpy as np
import pandas as pd

from bist_signal_bot.edge_validation.xsection import DailyContext
from bist_signal_bot.model_loop.daily_training import build_labels
from bist_signal_bot.tests.test_xsection_daily import make_panel

H = 5
GAP = (300, 303)  # close missing on rows 300..302 for one symbol -> exits nominally at 300..302 slide to 303


def _ctx(defer: bool):
    panel = make_panel(5, n_sym=30, days=500, momentum=0.0)
    sym = sorted(panel)[0]
    if defer:
        d = panel[sym].copy()
        d.iloc[GAP[0]:GAP[1], d.columns.get_loc("close")] = np.nan
        panel[sym] = d
    bm = pd.DataFrame({s: d["close"] for s, d in panel.items()}).mean(axis=1).ffill().bfill()
    return DailyContext.from_panel(panel, bm, min_adv=5e6), sym


def test_deferred_exit_extends_label_purge_window():
    ctx, sym = _ctx(True)
    lp = build_labels(ctx, H)
    j = ctx.symbols.index(sym)
    assert (lp.t1pos >= lp.pos + H).all()  # never earlier than nominal
    m = lp.j == j
    hit = m & (lp.pos + H >= GAP[0]) & (lp.pos + H < GAP[1])
    assert hit.any(), "scenario produced no deferred labels"
    assert (lp.t1pos[hit] == GAP[1]).all()
    assert (lp.t1pos[hit] > lp.pos[hit] + H).all()
    # other symbols / undeferred rows keep the nominal exit
    assert (lp.t1pos[~m] == lp.pos[~m] + H).all()


def test_no_train_test_label_overlap_with_deferred_exits():
    ctx, _ = _ctx(True)
    lp = build_labels(ctx, H)
    emb = 2
    deferred = lp.t1pos > lp.pos + H
    assert deferred.any()
    for r in range(GAP[0] - 6, GAP[0] + 8):
        train = lp.t1pos < r - emb          # purge by realized exit
        test = lp.pos >= r
        if not train.any() or not test.any():
            continue
        # no train label's [pos, t1pos] span reaches the test region
        assert lp.t1pos[train].max() < lp.pos[test].min()
        # purging by nominal t1 would have leaked a deferred label whose realized exit lies past the cut
        nominal_train = (lp.pos + H) < r - emb
        leaked = nominal_train & ~train
        assert (lp.t1pos[leaked] >= r - emb).all()
