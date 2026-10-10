"""Daily Turkish paper trade receipt (islem fisi) + order-intent journal for the forward shadow system.

Simulation only. No real order is ever sent; intents are paper records, there is no broker code."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np

from bist_signal_bot.forward import NO_ORDER
from bist_signal_bot.forward.chain import HashChain
from bist_signal_bot.forward.config import PRIMARY, ForwardConfig, load_portfolios, portfolio_tier, utcnow_iso

NO_ORDER_TR = "Gerçek emir gönderilmedi. Yalnız paper/simülasyon."
STALE_TEXT = "KARAR YOK (veri bayat)"
INTENT_TYPE = "intent"
CHAIN_TYPES = ("header", "freeze", "decision", "entry", "exit", INTENT_TYPE)  # record types written by forward/


def intents_path(cfg: ForwardConfig) -> Path:
    return cfg.forward_dir / "intents.jsonl"


def receipts_dir(cfg: ForwardConfig) -> Path:
    return cfg.forward_dir / "receipts"


def receipt_tiers(cfg: ForwardConfig) -> set:
    return {t.strip() for t in cfg.s("FORWARD_RECEIPT_TIERS", "watch").split(",") if t.strip()}


def _last_run(cfg: ForwardConfig) -> Optional[dict]:
    if not cfg.runs_path.exists():
        return None
    for ln in reversed(cfg.runs_path.read_text(encoding="utf-8").splitlines()):
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("as_of"):
            return r
    return None


def _cost_fn(cfg):
    try:
        from bist_signal_bot.forward.shadow import cost_models
        cm = cost_models(cfg.settings)[PRIMARY]
    except Exception:  # noqa: BLE001
        return lambda price, value, adv, side: 0.0

    def fn(price, value, adv, side):
        try:
            b = float(cm.cost_bps(price, value, adv, side))
        except Exception:  # noqa: BLE001
            return 0.0
        return 0.0 if b != b else b * value / 1e4
    return fn


def _plan(picks: list, capital: float, buffer: float):
    from bist_signal_bot.risk.daily_overlay import to_lots
    if not picks:
        return None
    w = 1.0 / len(picks)
    return to_lots({p["symbol"]: w for p in picks}, {p["symbol"]: p["price"] for p in picks}, capital,
                   max_names=len(picks), per_name_cap=1.0, min_order_value=0.0, lot_size=1, price_buffer=buffer)


def _empty(pid, as_of, tier, capital, status, warnings):
    return {"portfolio_id": pid, "as_of": as_of, "tier": tier, "status": status, "capital": capital, "buy": [],
            "sell": [], "hold": [], "cash": None, "invested": 0.0, "residual": None, "warnings": warnings,
            "disclaimer": NO_ORDER, "disclaimer_tr": NO_ORDER_TR}


def build_receipt(cfg: ForwardConfig, portfolio_id: str, as_of=None) -> dict:
    """Target picks vs previous holdings -> BUY/SELL lists. Fail-closed: stale/missing data -> no decisions."""
    capital = cfg.f("FORWARD_CAPITAL_TRY", 100000.0)
    buffer = cfg.f("FORWARD_RECEIPT_PRICE_BUFFER", 0.005)
    doc = load_portfolios(cfg)
    p = next((x for x in doc["portfolios"] if x["id"] == portfolio_id), None)
    if p is None:
        raise KeyError(f"unknown portfolio {portfolio_id}")
    tier = portfolio_tier(p)
    run = _last_run(cfg)
    want = str(as_of) if as_of else (run or {}).get("as_of")
    if run is None or not want or run.get("freshness_gate") != "PASS" or str(run.get("as_of")) < want:
        return _empty(portfolio_id, want, tier, capital, "STALE", [STALE_TEXT])
    dec_ch, out_ch = HashChain(cfg.decisions_path), HashChain(cfg.outcomes_path)
    if not dec_ch.verify()["ok"] or not out_ch.verify()["ok"]:
        return _empty(portfolio_id, want, tier, capital, "STALE", ["zincir bozuk; " + STALE_TEXT])
    decs = sorted((d for d in dec_ch.iter_type("decision") if d["portfolio_id"] == portfolio_id),
                  key=lambda d: d["as_of"])
    cur = next((d for d in decs if d["as_of"] == want), None)
    if cur is None:
        return _empty(portfolio_id, want, tier, capital, "NO_REBALANCE", ["Bugün yeni karar yok (rebalans günü değil)."])
    entries = {e["decision_hash"]: e for e in out_ch.iter_type("entry")}
    exits = {e["decision_hash"] for e in out_ch.iter_type("exit")}
    prev = next((d for d in reversed(decs) if d["as_of"] < want), None)
    held: dict = {}
    matured = False
    if prev is not None and prev["hash"] not in exits:
        ent = entries.get(prev["hash"])
        if ent is not None:
            fills = (ent.get("fills") or {}).get(PRIMARY) or {}
            held = {s: int(f.get("shares") or 0) for s, f in fills.items() if int(f.get("shares") or 0) > 0}
        else:
            pl = _plan(prev["picks"], capital, buffer)
            held = dict(pl.shares) if pl else {}
        matured = int(np.busday_count(prev["as_of"], want)) >= int(prev.get("horizon") or p["horizon"])
    plan = _plan(cur["picks"], capital, buffer)
    target = dict(plan.shares) if plan else {}
    px = {x["symbol"]: x for x in cur["picks"]}
    pxp = {x["symbol"]: x for x in (prev["picks"] if prev else [])}
    cost = _cost_fn(cfg)
    buy, sell, hold, warn = [], [], [], []
    for s in sorted(target):
        d = target[s] - held.get(s, 0)
        if d > 0:
            v = d * px[s]["price"]
            buy.append({"symbol": s, "qty": d, "ref_price": px[s]["price"], "value": v,
                        "est_cost": cost(px[s]["price"], v, px[s].get("adv", 0.0), "buy"),
                        "limit_price": round(px[s]["price"] * (1 + buffer), 2)})
        elif d < 0:
            v = -d * px[s]["price"]
            sell.append({"symbol": s, "qty": -d, "ref_price": px[s]["price"], "value": v,
                         "est_cost": cost(px[s]["price"], v, px[s].get("adv", 0.0), "sell"),
                         "reason": "yeniden dengeleme (fazla adet)"})
        if held.get(s, 0) and d <= 0:
            hold.append({"symbol": s, "qty": min(held[s], target[s])})
    for s in sorted(set(held) - set(target)):
        ref = (pxp.get(s) or {}).get("price") or 0.0
        v = held[s] * ref
        sell.append({"symbol": s, "qty": held[s], "ref_price": ref, "value": v,
                     "est_cost": cost(ref, v, (pxp.get(s) or {}).get("adv", 0.0), "sell"),
                     "reason": "ufuk dolumu" if matured else "çıkış (hedef dışı)"})
    if plan:
        warn += [f"{s}: plana alınmadı ({why})" for s, why in plan.dropped.items()] + list(plan.notes)
    invested = float(plan.invested) if plan else 0.0
    if sum(b["value"] for b in buy) > capital + 1e-6:
        raise AssertionError("buy list exceeds capital")
    warn.append("Fiyatlar as_of kapanışıdır; giriş ertesi seans açılışı, tutarlar tahmindir.")
    return {"portfolio_id": portfolio_id, "as_of": want, "tier": tier, "status": "OK", "capital": capital,
            "decision_hash": cur["hash"], "horizon": cur.get("horizon"), "buy": buy, "sell": sell, "hold": hold,
            "target_shares": target, "invested": invested, "residual": capital - invested, "cash": capital - invested,
            "price_buffer": buffer, "warnings": warn, "disclaimer": NO_ORDER, "disclaimer_tr": NO_ORDER_TR}


def write_intents(cfg: ForwardConfig, receipt: dict) -> list:
    """Append paper order intents (idempotent per decision) to the hash-chained intents journal."""
    if receipt.get("status") != "OK":
        return []
    ch = HashChain(intents_path(cfg))
    if ch.verify()["n"] == 0:
        ch.append("header", {"ledger": "intents", "created_at": utcnow_iso(), "disclaimer": NO_ORDER})
    done = {(r["portfolio_id"], r["decision_hash"]) for r in ch.iter_type(INTENT_TYPE)}
    if (receipt["portfolio_id"], receipt["decision_hash"]) in done:
        return []
    out = []
    for side, rows in (("SELL", receipt["sell"]), ("BUY", receipt["buy"])):
        for r in rows:
            out.append(ch.append(INTENT_TYPE, {
                "portfolio_id": receipt["portfolio_id"], "as_of": receipt["as_of"],
                "decision_hash": receipt["decision_hash"], "side": side, "symbol": r["symbol"], "qty": r["qty"],
                "ref_price": r["ref_price"], "limit_price": r.get("limit_price", r["ref_price"]),
                "reason": r.get("reason", "hedef portföy"), "recorded_at": utcnow_iso(),
                "no_real_order_sent": True, "disclaimer": NO_ORDER}))
    return out


def _tl(x) -> str:
    return "-" if x is None else f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def render_receipt_tr(r: dict) -> str:
    L = ["=" * 64, "GÜNLÜK PAPER İŞLEM FİŞİ (simülasyon)", "=" * 64,
         f"Tarih (as_of) : {r.get('as_of')}", f"Portföy       : {r['portfolio_id']} [{r.get('tier')}]",
         f"Sermaye       : {_tl(r['capital'])} TL"]
    if r["status"] == "STALE":
        L += ["", STALE_TEXT, "Hiçbir işlem listelenmedi."]
    elif r["status"] == "NO_REBALANCE":
        L += ["", "Bugün yeni karar yok; işlem listelenmedi."]
    else:
        L += ["", "AL (ne alacağım)", f"{'Sembol':<10}{'Adet':>8}{'Tah.Fiyat':>12}{'Tutar TL':>14}{'Tah.Maliyet':>13}"]
        L += [f"{b['symbol']:<10}{b['qty']:>8}{_tl(b['ref_price']):>12}{_tl(b['value']):>14}{_tl(b['est_cost']):>13}"
              for b in r["buy"]] or ["(yok)"]
        L += ["", "SAT (ne satacağım)", f"{'Sembol':<10}{'Adet':>8}{'Tah.Fiyat':>12}  Neden"]
        L += [f"{s['symbol']:<10}{s['qty']:>8}{_tl(s['ref_price']):>12}  {s['reason']}" for s in r["sell"]] or ["(yok)"]
        if r["hold"]:
            L += ["", "TUT: " + ", ".join(f"{h['symbol']}({h['qty']})" for h in r["hold"])]
        L += ["", f"Hedef yatırım : {_tl(r['invested'])} TL (tam hisse)", f"Nakit         : {_tl(r['cash'])} TL",
              f"Yuvarlama artığı: {_tl(r['residual'])} TL (tam hisse, lot=1)"]
    if r["warnings"]:
        L += ["", "Uyarılar:"] + [f"- {w}" for w in r["warnings"]]
    L += ["", NO_ORDER_TR, NO_ORDER]
    return "\n".join(L) + "\n"


def run_receipts(cfg: ForwardConfig, as_of=None, portfolio: Optional[str] = None, journal: bool = True) -> list:
    """Build, journal and save receipts for the configured tiers. Returns [(receipt, path)]."""
    if not cfg.portfolios_versions():  # nothing frozen yet -> nothing to report (fail closed)
        return []
    doc = load_portfolios(cfg)
    tiers = receipt_tiers(cfg)
    out = []
    d = receipts_dir(cfg)
    d.mkdir(parents=True, exist_ok=True)
    for p in doc["portfolios"]:
        if (portfolio and p["id"] != portfolio) or portfolio_tier(p) not in tiers:
            continue
        r = build_receipt(cfg, p["id"], as_of)
        if journal:
            r["intents_written"] = len(write_intents(cfg, r))
        path = d / f"{r.get('as_of') or 'unknown'}_{p['id']}.txt"
        path.write_text(render_receipt_tr(r), encoding="utf-8")
        out.append((r, path))
    return out
