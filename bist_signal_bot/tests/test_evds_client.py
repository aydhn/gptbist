"""EVDS client tests: mocked HTTP only (no network), key never leaks."""
import json

import numpy as np
import pandas as pd
import pytest

from bist_signal_bot.daily import macro
from bist_signal_bot.data_sources import evds_client as E
from bist_signal_bot.edge_validation.cash_benchmark import daily_cash_returns, daily_cash_returns_series
from bist_signal_bot.edge_validation.real_returns import build_real_report

KEY = "SECRETKEY1234567890"


def _items(code, rows):
    col = code.replace(".", "_")
    return json.dumps({"totalCount": len(rows), "items": [{"Tarih": d, col: v} for d, v in rows]})


class FakeHttp:
    def __init__(self, routes=None, fail=0, html=False, status=200):
        self.routes, self.calls, self.fail, self.html, self.status = routes or {}, [], fail, html, status

    def __call__(self, url, headers, timeout):
        self.calls.append((url, dict(headers)))
        if self.fail > 0:
            self.fail -= 1
            raise ConnectionError(f"boom key={headers['key']}")
        if self.html:
            return 200, "<html>evds2</html>"
        if self.status != 200:
            return self.status, ""
        for k, v in self.routes.items():
            if k in url:
                return 200, v
        return 200, json.dumps({"items": []})


def _client(tmp_path, http, **kw):
    sleeps = []
    c = E.EVDSClient(KEY, directory=tmp_path, http_get=http, sleep=sleeps.append, **kw)
    c.sleeps = sleeps
    return c


def test_key_in_header_not_url_and_parsing(tmp_path):
    code = E.CPI_NEW
    http = FakeHttp({code: _items(code, [("2025-1", "100.0"), ("2025-2", "103.1"), ("2025-3", None)])})
    s = _client(tmp_path, http).fetch_series(code, "01-01-2025", "10-10-2026")
    assert list(s.index) == [pd.Timestamp("2025-01-01"), pd.Timestamp("2025-02-01")]
    url, headers = http.calls[0]
    assert headers == {"key": KEY} and KEY not in url
    assert url.startswith("https://evds3.tcmb.gov.tr/igmevdsms-dis/series=TP.TUKFIY2025.GENEL&startDate=01-01-2025")
    assert url.endswith("&type=json")


def test_retry_backoff_then_success_and_masking(tmp_path):
    code = E.TLREF
    http = FakeHttp({code: _items(code, [("02-01-2025", "45.0")])}, fail=2)
    c = _client(tmp_path, http)
    s = c.fetch_series(code, "01-01-2025", "10-01-2025")
    assert len(http.calls) == 3 and len(s) == 1
    http2 = FakeHttp(fail=5)
    c2 = _client(tmp_path / "b", http2)
    with pytest.raises(E.EVDSError) as ei:
        c2.fetch_series(code, "01-01-2025", "10-01-2025")
    assert len(http2.calls) == 3 and KEY not in str(ei.value)


def test_html_answer_is_error(tmp_path):
    c = _client(tmp_path, FakeHttp(html=True))
    with pytest.raises(E.EVDSError, match="non-JSON"):
        c.fetch_series(E.TLREF, "01-01-2025", "10-01-2025")
    with pytest.raises(E.EVDSError, match="HTTP 403"):
        _client(tmp_path / "x", FakeHttp(status=403)).fetch_series(E.TLREF, "01-01-2025", "10-01-2025")


def test_rate_limit_sleeps_between_requests(tmp_path):
    t = [100.0]
    http = FakeHttp({E.TLREF: _items(E.TLREF, [("02-01-2025", "45")])})
    sleeps = []
    c = E.EVDSClient(KEY, directory=tmp_path, http_get=http, sleep=sleeps.append, clock=lambda: t[0])
    E._last_call[0] = float("-inf")
    c.fetch_series(E.TLREF, "01-01-2025", "10-01-2025", use_cache=False)
    c.fetch_series(E.TLREF, "01-01-2025", "11-01-2025", use_cache=False)  # same clock -> must wait 1 s
    assert any(abs(x - 1.0) < 1e-9 for x in sleeps)


def test_cache_labelled_and_reused_and_stale_fallback(tmp_path):
    http = FakeHttp({E.TLREF: _items(E.TLREF, [("02-01-2025", "45")])})
    c = _client(tmp_path, http)
    c.fetch_series(E.TLREF, "01-01-2025", "10-01-2025")
    c.fetch_series(E.TLREF, "01-01-2025", "10-01-2025")
    assert len(http.calls) == 1  # second call from cache
    f = next((tmp_path / "evds_cache").glob("*.json"))
    meta = json.loads(f.read_text(encoding="utf-8"))
    assert meta["source"] == "TCMB-EVDS3" and meta["fetched_at"] and KEY not in f.read_text(encoding="utf-8")
    # expired ttl + failing network -> stale cache used
    c2 = _client(tmp_path, FakeHttp(fail=9), cache_ttl_hours=-1)
    assert len(c2.fetch_series(E.TLREF, "01-01-2025", "10-01-2025")) == 1


def test_missing_key_clear_error():
    class S:
        EVDS_API_KEY = ""
    with pytest.raises(E.EVDSError, match="EVDS_API_KEY is not set"):
        E.get_api_key(S())


def test_find_series_and_policy_rate_none(tmp_path):
    rows = [{"SERIE_CODE": "TP.X1", "SERIE_NAME": "TCMB Bir Hafta Vadeli Repo İhale Faizi"},
            {"SERIE_CODE": "TP.X2", "SERIE_NAME": "Other"}]
    c = _client(tmp_path, FakeHttp({"serieList": json.dumps(rows)}))
    assert c.find_series("bie_ptbfon", "bir hafta", "repo") == "TP.X1"
    assert c.find_series("bie_ptbfon", "yok") is None
    c2 = _client(tmp_path, FakeHttp({"serieList": json.dumps([{"SERIE_CODE": "A", "SERIE_NAME": "zzz"}])}))
    assert c2.find_policy_rate_series() is None


def test_splice_cpi_continuous_and_build_writes_loadable_csv(tmp_path):
    old_idx = pd.date_range("2003-01-01", "2026-01-01", freq="MS")
    old = pd.Series(100 * 1.03 ** np.arange(len(old_idx)), index=old_idx)
    ratio_true = 0.02
    new_idx = pd.date_range("2025-01-01", "2026-01-01", freq="MS")
    new = old.loc[new_idx] * ratio_true
    http = FakeHttp({
        E.CPI_OLD: _items(E.CPI_OLD, [(f"{d.year}-{d.month}", f"{v:.6f}") for d, v in old.items()]),
        E.CPI_NEW: _items(E.CPI_NEW, [(f"{d.year}-{d.month}", f"{v:.6f}") for d, v in new.items()]),
    })
    c = _client(tmp_path, http)
    s = c.build_cpi(end="10-10-2026")
    assert s.index[0] == pd.Timestamp("2003-01-01") and s.index.is_monotonic_increasing
    assert s.loc["2025-01-01"] == pytest.approx(new.iloc[0])
    # growth continuous across the splice point
    g = s.pct_change().dropna()
    assert g.max() == pytest.approx(0.03, rel=1e-3) and g.min() == pytest.approx(0.03, rel=1e-3)
    # file compatible with daily.macro.read_cpi_csv
    back = macro.read_cpi_csv(tmp_path / "cpi_tr.csv")
    assert len(back) == len(s)
    assert list(pd.read_csv(tmp_path / "cpi_tr.csv").columns) == ["date", "index"]
    # load_cpi prefers the new local file
    got, src = macro.load_cpi(directory=tmp_path, allow_fetch=False)
    assert src.startswith("local:") and got.iloc[-1] == pytest.approx(new.iloc[-1])
    assert "KEY" not in (tmp_path / "cpi_tr.csv").read_text().upper()


def test_splice_cpi_no_overlap_raises():
    a = pd.Series([1.0], index=pd.to_datetime(["2020-01-01"]))
    b = pd.Series([1.0], index=pd.to_datetime(["2025-01-01"]))
    with pytest.raises(E.EVDSError):
        E.splice_cpi(a, b)


def test_build_cash_rate_file_and_loader(tmp_path):
    tl = _items(E.TLREF, [("02-01-2024", "45.0"), ("03-01-2024", "46.0")])
    ao = _items(E.AOFM, [("02-01-2023", "20.0"), ("02-01-2024", "44.0")])
    c = _client(tmp_path, FakeHttp({E.TLREF: tl, E.AOFM: ao}))
    s = c.build_cash_rate(end="10-10-2026")
    assert list(s.round(4)) == [0.20, 0.45, 0.46]  # AOFM only before TLREF starts; percent -> fraction
    assert list(pd.read_csv(tmp_path / "tlref.csv").columns) == ["date", "rate_annual"]
    loaded = E.load_cash_rate_series(directory=tmp_path)
    assert loaded.iloc[-1] == pytest.approx(0.46)
    assert E.load_cash_rate_series(directory=tmp_path / "none") is None


def test_time_varying_cash_returns_causal_and_default_unchanged():
    idx = pd.bdate_range("2024-01-01", "2024-03-29")
    const = daily_cash_returns(idx, 0.37, 0.0)
    flat = daily_cash_returns_series(idx, pd.Series([0.37], index=[pd.Timestamp("2023-12-01")]), 0.0)
    assert np.allclose(const, flat)
    step = pd.Series([0.10, 0.50], index=pd.to_datetime(["2023-12-01", "2024-02-01"]))
    r = daily_cash_returns_series(idx, step, 0.0)
    assert r.loc["2024-02-01"] == pytest.approx((1.10) ** (1 / 365) - 1)  # rate known at previous bar (Jan 31)
    assert r.loc["2024-02-02"] == pytest.approx((1.50) ** (1 / 365) - 1)
    with pytest.raises(ValueError):
        daily_cash_returns_series(idx, pd.Series([0.1], index=[pd.Timestamp("2024-02-01")]), 0.0)


class _Ctx:
    def __init__(self, idx, series=None, rate=0.37):
        self.benchmark = self.usdtry = None
        self.cash_rate = rate
        if series is not None:
            self.cash_rate_series = series


def test_real_report_uses_series_only_when_given():
    idx = pd.bdate_range("2019-01-01", "2020-12-31")
    r = pd.Series(0.0005, index=idx)
    cpi = pd.Series(100 * 1.02 ** np.arange(36), index=pd.date_range("2018-01-01", periods=36, freq="MS"))
    base = build_real_report(r, _Ctx(idx), cpi, settings=None)["comparators"]["cash_gross"]["cagr"]
    same = build_real_report(r, _Ctx(idx, pd.Series([0.37], index=[pd.Timestamp("2018-01-01")])), cpi)
    assert same["comparators"]["cash_gross"]["cagr"] == pytest.approx(base)
    low = build_real_report(r, _Ctx(idx, pd.Series([0.10], index=[pd.Timestamp("2018-01-01")])), cpi)
    assert low["comparators"]["cash_gross"]["cagr"] < base


def test_cli_without_key_errors_cleanly(monkeypatch, capsys):
    from bist_signal_bot.cli import macro_cli
    monkeypatch.setattr(E, "get_api_key", lambda settings=None: (_ for _ in ()).throw(E.EVDSError("EVDS_API_KEY is not set")))
    assert macro_cli.main(["evds-sync"]) == 2
    assert "EVDS_API_KEY is not set" in capsys.readouterr().out


def test_chunked_fetch_beats_1000_row_truncation_and_warns(tmp_path, caplog):
    import logging
    days = pd.bdate_range("2010-01-01", "2016-12-31")  # ~1826 rows; server returns only the first 1000 of a range
    col = E.TLREF.replace(".", "_")

    def http(url, headers, timeout):
        import re as _re
        m = _re.search(r"startDate=(\d\d-\d\d-\d{4})&endDate=(\d\d-\d\d-\d{4})", url)
        a, b = (pd.to_datetime(x, format="%d-%m-%Y") for x in m.groups())
        sel = days[(days >= a) & (days <= b)][:1000]
        return 200, json.dumps({"items": [{"Tarih": d.strftime("%d-%m-%Y"), col: "10.0"} for d in sel]})

    c = _client(tmp_path, http)
    with caplog.at_level(logging.WARNING):
        s = c.fetch_series(E.TLREF, "01-01-2010", "31-12-2016")
    assert len(s) == len(days) and s.index.is_unique and s.index[0] == days[0] and s.index[-1] == days[-1]
    # a single un-chunked request would have been cut at 1000 rows
    s1 = _client(tmp_path / "x", http).fetch_series(E.TLREF, "01-01-2010", "31-12-2016", chunk_years=50)
    assert len(s1) == 1000
    assert any("truncated" in r.message for r in caplog.records)
