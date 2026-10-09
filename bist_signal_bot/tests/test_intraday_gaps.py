from datetime import date

import pandas as pd

from functools import partial

from bist_signal_bot.intraday import gaps as _g
from bist_signal_bot.intraday import sessions as _s

# Legacy tests target the exchange grid; yahoo tests are at the bottom.
detect_gaps = partial(_g.detect_gaps, vendor="exchange")
detect_gaps_range = partial(_g.detect_gaps_range, vendor="exchange")
expected_bar_starts = partial(_s.expected_bar_starts, vendor="exchange")

D = date(2026, 6, 1)


def test_full_coverage():
    r = detect_gaps(expected_bar_starts(D, 15), D, 15)
    assert (r.expected_count, r.present_count, r.coverage) == (32, 32, 1.0)
    assert r.missing == [] and r.suspected_halt_runs == []


def test_halt_run_detected():
    bars = expected_bar_starts(D, 15)
    kept = bars[:10] + bars[14:]  # 4 missing mid-session
    r = detect_gaps(kept, D, 15)
    assert len(r.missing) == 4
    assert len(r.suspected_halt_runs) == 1 and len(r.suspected_halt_runs[0]) == 4
    assert r.coverage == 28 / 32


def test_short_gap_not_halt_and_edges_not_halt():
    bars = expected_bar_starts(D, 15)
    r = detect_gaps(bars[:10] + bars[12:], D, 15)  # 2 missing
    assert len(r.missing) == 2 and r.suspected_halt_runs == []
    r = detect_gaps(bars[5:], D, 15)  # leading gap of 5, no bars before
    assert len(r.missing) == 5 and r.suspected_halt_runs == []


def test_empty_and_pandas_index_and_offgrid():
    r = detect_gaps([], D, 60)
    assert r.present_count == 0 and r.coverage == 0.0
    idx = pd.DatetimeIndex(expected_bar_starts(D, 60)[:3])
    assert detect_gaps(idx, D, 60).present_count == 3
    naive = [b.replace(tzinfo=None) for b in expected_bar_starts(D, 60)]
    assert detect_gaps(naive, D, 60).present_count == 8
    assert detect_gaps([pd.Timestamp("2026-06-01 10:07")], D, 60).present_count == 0


def test_non_trading_day_report():
    r = detect_gaps([], date(2026, 6, 6), 15)
    assert r.expected_count == 0 and r.coverage == 1.0


def test_range_skips_non_trading_days():
    ts = expected_bar_starts(date(2026, 6, 8), 60)
    reports = detect_gaps_range(ts, date(2026, 6, 5), date(2026, 6, 9), 60)
    assert [r.day for r in reports] == [date(2026, 6, 5), date(2026, 6, 8), date(2026, 6, 9)]
    assert [r.present_count for r in reports] == [0, 8, 0]
    # Sat/Sun and holiday skipped
    assert len(detect_gaps_range([], date(2026, 7, 13), date(2026, 7, 19), 60)) == 4


def test_yahoo_default_grid():
    bars = _s.expected_bar_starts(D, 15)
    r = _g.detect_gaps(bars, D, 15)
    assert (r.expected_count, r.present_count, r.coverage) == (33, 33, 1.0)
    # exchange-grid timestamps are flagged against the yahoo grid (09:45 missing)
    r = _g.detect_gaps(expected_bar_starts(D, 15), D, 15)
    assert r.present_count == 32 and len(r.missing) == 1
    assert _g.detect_gaps([], D, 60).expected_count == 9
    assert _g.detect_gaps([], D, 5).expected_count == 97
    assert len(_g.detect_gaps_range([], D, D, 15)) == 1
