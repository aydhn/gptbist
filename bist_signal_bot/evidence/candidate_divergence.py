"""Per-candidate live (forward shadow) vs backtest-replay divergence. Simulation only; no real order is ever sent.

Live = what the forward chain persisted (entry fills frozen at decision time + the NAV csv derived from them).
Modeled = the SAME frozen decisions re-simulated over the SAME live dates with ``forward.sim.replay`` (the shared
``fills_daily``/``DailyCostModel`` path of edge_validation) on the CURRENT archive with no persisted fills, i.e. the
backtest-style fill at the open. No new fill model. Invalidation thresholds are frozen in config/defaults.py and are
never re-tuned.
"""
from __future__ import annotations

import json
import math
from typing import Optional

import numpy as np
import pandas as pd

from bist_signal_bot.forward import NO_ORDER
from bist_signal_bot.forward.chain import HashChain
from bist_signal_bot.forward.config import PRIMARY, ForwardConfig, load_portfolios, portfolio_tier, utcnow_iso

UNFILLED_REASONS = ("no_open_or_no_volume", "unfillable_entry_price_limit", "price_limit_flag")
NOT_COMPUTABLE = ["event_net_excess<40bps (~300 sessions)", "NAV excess Sharpe/CAGR (12 months)",
                  "ADV>=5e7 trim5<0", "P&L concentration in top-3 symbols"]


def _maxdd(nav: pd.Series) -> float:
    return float((1.0 - nav / nav.cummax()).max()) if len(nav) else 0.0


def _thresholds(cfg: ForwardConfig) -> dict:
    return {"max_fill_gap_bps": cfg.f("FORWARD_DIV_MAX_FILL_GAP_BPS", 30.0),
            "max_unfilled_pct": cfg.f("FORWARD_DIV_MAX_UNFILLED_PCT", 0.08),
            "sessions": cfg.i("FORWARD_DIV_SESSIONS", 120),
            "max_dd": cfg.f("FORWARD_DIV_MAX_DD", 0.35)}


def _fill_stats(live_entries: list, model_entries: dict) -> dict:
    gaps, unfilled, total = [], 0, 0
    for e in live_entries:
        if e.get("blocked"):
            continue
        fills = (e.get("fills") or {}).get(PRIMARY) or {}
        dropped = (e.get("dropped") or {}).get(PRIMARY) or []
        total += len(fills) + len(dropped)
        unfilled += sum(1 for _, why in dropped if why in UNFILLED_REASONS)
        m = ((model_entries.get(e["decision_hash"]) or {}).get("fills") or {}).get(PRIMARY) or {}
        for sym, f in fills.items():
            if sym in m and m[sym]["px"] > 0:
                gaps.append((f["px"] / m[sym]["px"] - 1.0) * 1e4)  # buy: positive = live fill worse than model
    g = np.asarray(gaps, float)
    return {"entries_live": total, "unfilled_entries": unfilled,
            "unfilled_pct": (unfilled / total) if total else None, "fills_compared": int(len(g)),
            "fill_gap_bps_mean": float(g.mean()) if len(g) else None,
            "fill_gap_bps_mean_abs": float(np.abs(g).mean()) if len(g) else None,
            "fill_gap_bps_max": float(g.max()) if len(g) else None}


def _checks(cfg: ForwardConfig, live_days: int, fill: dict, live_nav: pd.DataFrame) -> list:
    th = _thresholds(cfg)
    out = []
    g = fill["fill_gap_bps_mean"]
    out.append({"id": "fill_gap", "rule": f"mean live open fill worse than model > {th['max_fill_gap_bps']:g} bps",
                "value": g, "breached": None if g is None else bool(g > th["max_fill_gap_bps"])})
    u = fill["unfilled_pct"]
    out.append({"id": "unfilled_entries", "rule": f"unfilled entries > {th['max_unfilled_pct']:.0%}", "value": u,
                "breached": None if u is None else bool(u > th["max_unfilled_pct"])})
    n = th["sessions"]
    rule = f"cum. excess vs EW < 0 AND maxDD > {th['max_dd']:.0%} after {n} sessions"
    if live_days < n or "ew_nav" not in live_nav:
        out.append({"id": "cum_excess_dd", "rule": rule, "value": None, "breached": None,
                    "note": f"needs >= {n} live sessions (have {live_days})"})
    else:
        nav, ew = live_nav[f"nav_{PRIMARY}"].tail(n + 1), live_nav["ew_nav"].tail(n + 1)
        ex, dd = float(nav.iloc[-1] / nav.iloc[0] - ew.iloc[-1] / ew.iloc[0]), _maxdd(nav)
        out.append({"id": "cum_excess_dd", "rule": rule, "value": {"cum_excess": ex, "max_dd": dd},
                    "breached": bool(ex < 0 and dd > th["max_dd"])})
    return out


def _scrub(o):
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, dict):
        return {k: _scrub(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_scrub(v) for v in o]
    return o


def candidate_divergence(cfg: ForwardConfig, portfolio_id: str, ctx=None, archive=None) -> dict:
    """Divergence report dict for one frozen forward portfolio. Status NO_LIVE_DATA when < 1 live day."""
    doc = load_portfolios(cfg)
    p = next((x for x in doc["portfolios"] if x["id"] == portfolio_id), None)
    if p is None:
        raise KeyError(f"unknown portfolio {portfolio_id}")
    rep = {"portfolio_id": portfolio_id, "family": p["family"], "params": p["params"], "horizon": p["horizon"],
           "tier": portfolio_tier(p), "generated_at": utcnow_iso(), "disclaimer": NO_ORDER,
           "thresholds": _thresholds(cfg), "not_computable": NOT_COMPUTABLE,
           "fill_note": "live fill = entry px persisted at first run; modeled = same decision re-filled on the current "
                        "archive (differs only if history was restated or the live run used different bars)"}
    f = cfg.nav_dir / f"{portfolio_id}.csv"
    live = pd.read_csv(f, index_col=0, parse_dates=True) if f.exists() else None
    days = (len(live) - 1) if live is not None else 0
    rep["live_days"] = max(days, 0)
    decs = []
    if days >= 1:
        decs = sorted((d for d in HashChain(cfg.decisions_path).iter_type("decision")
                       if d["portfolio_id"] == portfolio_id), key=lambda r: r["as_of"])
    if days < 1 or not decs:
        return {**rep, "status": "NO_LIVE_DATA", "checks": [], "any_breach": None}
    live_entries = [e for e in HashChain(cfg.outcomes_path).iter_type("entry") if e["portfolio_id"] == portfolio_id]
    from bist_signal_bot.forward.shadow import build_ctx, cost_models
    from bist_signal_bot.forward.sim import replay
    if ctx is None:
        from bist_signal_bot.intraday.archive import BarArchive
        own = archive is None
        if own:
            archive = BarArchive(path=cfg.archive_path, settings=cfg.settings)
        try:
            ctx = build_ctx(archive, cfg.settings)
        finally:
            if own:
                archive.close()
    model_entries: dict = {}
    mnav, _ = replay(ctx, decs, model_entries, {}, cost_models(cfg.settings), cfg.f("FORWARD_CAPITAL_TRY", 100000.0))
    rep.update(first_date=str(live.index[0].date()), last_date=str(live.index[-1].date()))
    col = f"nav_{PRIMARY}"
    idx = live.index.intersection(mnav.index) if mnav is not None else []
    if len(idx) < 2:
        return {**rep, "status": "NO_MODEL_DATA", "checks": [], "any_breach": None}
    L, M = live.loc[idx], mnav.loc[idx]
    gap = (L[col].pct_change() - M[col].pct_change()).iloc[1:].dropna()
    has_ew = "ew_nav" in L and "ew_nav" in M

    def cum(df):
        return float(df[col].iloc[-1] / df[col].iloc[0] - df["ew_nav"].iloc[-1] / df["ew_nav"].iloc[0])

    fill = _fill_stats(live_entries, model_entries)
    rep.update(
        status="OK", compared_days=int(len(gap)),
        live_cum_net_excess=cum(L) if has_ew else None, model_cum_net_excess=cum(M) if has_ew else None,
        live_total_return=float(L[col].iloc[-1] / L[col].iloc[0] - 1),
        model_total_return=float(M[col].iloc[-1] / M[col].iloc[0] - 1),
        mean_daily_gap_bps=float(gap.mean() * 1e4) if len(gap) else None,
        tracking_error_ann=float(gap.std(ddof=1) * math.sqrt(252)) if len(gap) > 1 else None,
        live_max_dd=_maxdd(live[col]), fill=fill)
    if has_ew:
        rep["cum_excess_gap"] = rep["live_cum_net_excess"] - rep["model_cum_net_excess"]
    rep["checks"] = _checks(cfg, rep["live_days"], fill, live)
    rep["any_breach"] = any(c["breached"] for c in rep["checks"] if c["breached"] is not None)
    return _scrub(rep)


def _fmt(x, n=2, pct=False):
    if x is None:
        return "n/a"
    return f"{x * 100:.{n}f}%" if pct else f"{x:.{n}f}"


def format_markdown(rep: dict) -> str:
    L = [f"# Aday Sapma Raporu (canlı gölge vs backtest tekrarı): {rep['portfolio_id']}", "",
         f"- Aile: {rep['family']} | Ufuk: {rep['horizon']} | Kademe: {rep['tier']}",
         f"- Durum: **{rep['status']}** | Canlı gün: {rep['live_days']}",
         f"- Gerçek emir gönderilmedi. {NO_ORDER}", ""]
    if rep["status"] != "OK":
        L += ["Canlı veri yok veya karşılaştırılamadı; rapor boş geçildi.", ""]
        return "\n".join(L)
    f = rep["fill"]
    L += ["## Getiri Karşılaştırması", "",
          f"- Kümülatif net fazla getiri (canlı): {_fmt(rep['live_cum_net_excess'], 3, True)}",
          f"- Kümülatif net fazla getiri (backtest tekrarı): {_fmt(rep['model_cum_net_excess'], 3, True)}",
          f"- Ortalama günlük getiri farkı: {_fmt(rep['mean_daily_gap_bps'])} bps",
          f"- İzleme hatası (yıllık): {_fmt(rep['tracking_error_ann'], 2, True)}",
          f"- Canlı azami düşüş: {_fmt(rep['live_max_dd'], 2, True)}", "",
          "## Dolum Farkları", "",
          f"- Karşılaştırılan dolum: {f['fills_compared']} | ortalama fark: {_fmt(f['fill_gap_bps_mean'])} bps "
          f"(mutlak {_fmt(f['fill_gap_bps_mean_abs'])}, azami {_fmt(f['fill_gap_bps_max'])})",
          f"- Dolmayan giriş: {f['unfilled_entries']}/{f['entries_live']} ({_fmt(f['unfilled_pct'], 1, True)})",
          f"- Not: {rep['fill_note']}", "", "## Geçersiz Kılma Eşikleri (dondurulmuş, yeniden ayar yok)", ""]
    for c in rep["checks"]:
        st = "BELİRSİZ" if c["breached"] is None else ("İHLAL" if c["breached"] else "tamam")
        L.append(f"- [{st}] {c['rule']} -> {c['value']}" + (f" ({c['note']})" if c.get("note") else ""))
    L += ["", "Bu veriyle hesaplanamayan eşikler: " + "; ".join(rep["not_computable"]), ""]
    return "\n".join(L)


def save_divergence(cfg: ForwardConfig, rep: dict):
    d = cfg.forward_dir / "divergence"
    d.mkdir(parents=True, exist_ok=True)
    stem = f"divergence_{rep['portfolio_id']}_{rep['generated_at'][:10].replace('-', '')}"
    (d / f"{stem}.json").write_text(json.dumps(rep, indent=2, sort_keys=True, default=str), encoding="utf-8")
    (d / f"{stem}.md").write_text(format_markdown(rep), encoding="utf-8")
    return d / f"{stem}.json", d / f"{stem}.md"


def run_all(cfg: ForwardConfig, portfolio_id: Optional[str] = None, save: bool = True) -> list:
    ids = [portfolio_id] if portfolio_id else [p["id"] for p in load_portfolios(cfg)["portfolios"]]
    out = []
    for pid in ids:
        r = candidate_divergence(cfg, pid)
        if save:
            r["json_path"], r["md_path"] = (str(x) for x in save_divergence(cfg, r))
        out.append(r)
    return out
