import pytest

from bist_signal_bot.risk.exit_rules import scan_daily_exit
from bist_signal_bot.risk.gap_risk import gap_exit_fill, FILLED, DEFERRED, NOT_TRIGGERED


def _bars(closes):
    # open of bar t = 1000 + t so the executing bar is identifiable
    return [1000.0 + i for i in range(len(closes))], closes


def test_fixed_stop_triggers_at_threshold_and_executes_next_open():
    o, c = _bars([100, 99, 95, 94, 90])
    r = scan_daily_exit(o, c, 0, stop_price=95)
    assert (r.reason, r.trigger_idx, r.exec_idx, r.exec_price) == ("FIXED_STOP", 2, 3, 1003.0)
    assert r.reduce_only


def test_fixed_stop_not_triggered_above_threshold():
    o, c = _bars([100, 99, 96, 97])
    assert scan_daily_exit(o, c, 0, stop_price=95).reason == "NONE"


def test_stop_on_last_bar_has_no_execution_price():
    o, c = _bars([100, 94])
    r = scan_daily_exit(o, c, 0, stop_price=95)
    assert r.reason == "FIXED_STOP" and r.exec_idx == -1 and r.exec_price is None


def test_trailing_ratchets_up_only_and_triggers_on_retrace():
    o, c = _bars([100, 110, 120, 115, 109, 108])  # trail 10% -> level 108 after the 120 close
    r = scan_daily_exit(o, c, 0, trail_pct=0.10)
    assert r.reason == "TRAILING_STOP" and r.trigger_idx == 5 and r.stop_level == pytest.approx(108.0)
    # 115 and 109 pulled back but stayed above the (never lowered) 108 level
    r2 = scan_daily_exit(o[:5], c[:5], 0, trail_pct=0.10)
    assert r2.reason == "NONE" and r2.stop_level == pytest.approx(108.0)


def test_trailing_level_never_decreases_on_lower_closes():
    o, c = _bars([100, 120, 112, 111])
    r = scan_daily_exit(o, c, 0, trail_pct=0.10)
    assert r.reason == "NONE" and r.stop_level == pytest.approx(108.0)


def test_no_same_bar_lookahead_new_high_cannot_trigger_itself():
    o, c = _bars([100, 150])
    assert scan_daily_exit(o, c, 0, trail_pct=0.05).reason == "NONE"


@pytest.mark.parametrize("horizon", [5, 10])
def test_time_exit_after_max_holding_sessions(horizon):
    c = [100.0] * 20
    o = [100.0 + i for i in range(20)]
    r = scan_daily_exit(o, c, 2, max_hold_sessions=horizon)
    assert r.reason == "TIME_EXIT"
    assert r.trigger_idx == 2 + horizon - 1 and r.exec_idx == 2 + horizon
    assert r.exec_price == o[2 + horizon]


def test_stop_beats_later_time_exit_and_combined_rules():
    o, c = _bars([100, 90, 100, 100])
    assert scan_daily_exit(o, c, 0, stop_price=92, max_hold_sessions=3).reason == "FIXED_STOP"


def test_validation():
    with pytest.raises(ValueError):
        scan_daily_exit([1.0], [1.0, 2.0], 0)
    with pytest.raises(ValueError):
        scan_daily_exit([1.0], [1.0], 0, trail_pct=1.5)


# ---------------------------------------------------------------- gap risk
def test_gap_through_stop_fills_at_open_worse_than_stop():
    r = gap_exit_fill(prev_close=100.0, open=92.0, stop_price=95.0, limit_pct=0.10)
    assert (r.status, r.price, r.gapped_through) == (FILLED, 92.0, True)
    assert r.price < 95.0


def test_locked_limit_down_open_defers_exit():
    r = gap_exit_fill(100.0, 90.0, 95.0, 0.10)  # floor = 90.00
    assert r.status == DEFERRED and r.price is None and r.reason == "locked_limit_down"


def test_no_gap_normal_fill_at_stop():
    r = gap_exit_fill(100.0, 99.0, 95.0, 0.10)
    assert (r.status, r.price, r.gapped_through) == (NOT_TRIGGERED, 95.0, False)


def test_short_side_mirrors_and_bad_input_defers():
    assert gap_exit_fill(100.0, 108.0, 105.0, 0.10, "SHORT").status == FILLED
    assert gap_exit_fill(100.0, 110.0, 105.0, 0.10, "SHORT").status == DEFERRED
    assert gap_exit_fill(100.0, float("nan"), 95.0, 0.10).status == DEFERRED
    with pytest.raises(ValueError):
        gap_exit_fill(100.0, 99.0, 95.0, 0.10, "FLAT")
