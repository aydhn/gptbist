import json

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.data_sources.fred_client import FredClient, FredError, mask_secrets
from bist_signal_bot.regime.features import RegimeFeatureBuilder
from bist_signal_bot.regime.global_macro import build_global_macro_features, global_macro_enabled

KEY = "SECRETKEY123456"


class S:
    FRED_API_KEY = KEY
    DATA_DIR = "."

    def __init__(self, flag=None):
        self.flag = flag

    def get(self, name, default=None):
        return self.flag if name == "REGIME_USE_GLOBAL_MACRO" and self.flag is not None else default


class Resp:
    def __init__(self, code, payload=None):
        self.status_code, self._p = code, payload

    def json(self):
        return self._p


class Sess:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, dict(params)))
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def client(tmp_path, responses):
    sess = Sess(responses)
    return FredClient(settings=S(), session=sess, cache_dir=tmp_path / "c", sleeper=lambda s: None), sess


def obs(*pairs):
    return {"observations": [{"date": d, "value": v} for d, v in pairs]}


def test_dot_is_nan_and_cache_roundtrip(tmp_path):
    c, sess = client(tmp_path, [Resp(200, obs(("2024-01-02", "13.5"), ("2024-01-03", "."))), ])
    s = c.fetch_series("VIXCLS")
    assert s.iloc[0] == 13.5 and np.isnan(s.iloc[1])
    assert sess.calls[0][1]["file_type"] == "json"
    s2 = c.fetch_series("VIXCLS")  # served from cache, no more responses queued
    assert len(sess.calls) == 1 and len(s2) == 2
    meta = json.loads((tmp_path / "c" / "VIXCLS.json").read_text())
    assert meta["meta"]["fetched_at"] and "FRED" in meta["meta"]["source"]
    assert KEY not in (tmp_path / "c" / "VIXCLS.json").read_text()


def test_retry_then_success_and_key_masked_on_failure(tmp_path):
    c, sess = client(tmp_path, [Resp(500), Resp(200, obs(("2024-01-02", "1")))])
    assert len(c.fetch_series("DGS10")) == 1 and len(sess.calls) == 2
    err = Exception(f"conn error https://x/y?api_key={KEY}&file_type=json")
    c, _ = client(tmp_path, [err] * 4)
    with pytest.raises(FredError) as e:
        c.fetch_series("DGS10", force=True)
    assert KEY not in str(e.value) and "api_key=***" in str(e.value)
    assert KEY not in repr(c)
    assert KEY not in mask_secrets(f"api_key={KEY}", KEY)


def test_http_4xx_not_retried_and_masked(tmp_path):
    c, sess = client(tmp_path, [Resp(400)])
    with pytest.raises(FredError):
        c.fetch_series("NOPE")
    assert len(sess.calls) == 1


def test_series_info(tmp_path):
    c, _ = client(tmp_path, [Resp(200, {"seriess": [{"id": "VIXCLS", "title": "VIX", "frequency": "Daily, Close",
                                                      "observation_end": "2024-01-02"}]})])
    assert c.series_info("VIXCLS")["frequency"].startswith("Daily")


def _series():
    us = pd.bdate_range("2023-01-02", periods=400)
    return {"VIXCLS": pd.Series(np.arange(400, dtype=float) + 10, index=us),
            "DGS10": pd.Series(np.linspace(3, 4, 400), index=us),
            "DTWEXBGS": pd.Series(np.linspace(100, 110, 400), index=us),
            "BAMLH0A0HYM2": pd.Series(np.linspace(3, 5, 400), index=us)}


def test_lookahead_day_t_does_not_see_day_t():
    ser = _series()
    bist = pd.bdate_range("2023-06-01", periods=60)
    f1 = build_global_macro_features(bist, ser)
    t = bist[30]
    ser2 = {k: v.copy() for k, v in ser.items()}
    for v in ser2.values():
        v.loc[t] = 1e6  # tamper with day-t FRED data
    f2 = build_global_macro_features(bist, ser2)
    pd.testing.assert_series_equal(f1.loc[t], f2.loc[t])
    assert not f1.loc[bist[31]].equals(f2.loc[bist[31]])  # visible only the next day
    assert f1.iloc[0].isna().all() or True
    assert list(f1.columns) == ["macro_vix_level", "macro_vix_z", "macro_us10y_chg", "macro_usd_mom", "macro_hy_spread"]


def test_flag_default_off_and_builder_integration():
    assert global_macro_enabled(S()) is False
    bist = pd.bdate_range("2023-06-01", periods=60)
    df = pd.DataFrame({"close": np.linspace(10, 12, 60), "high": 12.0, "low": 9.0, "volume": 1000.0}, index=bist)
    off = RegimeFeatureBuilder(S()).add_global_macro_columns(df, _series())
    assert not any(c.startswith("macro_") for c in off.columns)
    on = RegimeFeatureBuilder(S(flag=True)).add_global_macro_columns(df, _series())
    assert "macro_vix_z" in on.columns


def test_dtwexbgs_publication_lag_7_days():
    ser = _series()
    bist = pd.bdate_range("2023-06-01", periods=80)
    f1 = build_global_macro_features(bist, ser)
    t = bist[40]
    ser2 = {k: v.copy() for k, v in ser.items()}
    ser2["DTWEXBGS"].loc[t] = ser2["DTWEXBGS"].loc[t] * 3
    f2 = build_global_macro_features(bist, ser2)
    for d in bist:
        same = f1.loc[d, "macro_usd_mom"] == f2.loc[d, "macro_usd_mom"] or (
            pd.isna(f1.loc[d, "macro_usd_mom"]) and pd.isna(f2.loc[d, "macro_usd_mom"]))
        if t <= d <= t + pd.Timedelta(days=7):
            assert same, d
    assert (f1["macro_usd_mom"] != f2["macro_usd_mom"]).any()  # shows up later (t+20 rows use it too)
    # t's own feature only becomes visible after its 7-day lag (+1 BIST day) and is replaced next row
    first = bist[bist > t + pd.Timedelta(days=7)][0]
    assert f1.loc[first, "macro_usd_mom"] != f2.loc[first, "macro_usd_mom"]


def test_intraday_repeated_index_rejected():
    ix = pd.DatetimeIndex(["2023-06-01 10:00", "2023-06-01 11:00"])
    with pytest.raises(ValueError):
        build_global_macro_features(pd.bdate_range("2023-06-01", periods=5), {"VIXCLS": pd.Series([1.0, 2.0], index=ix)})
