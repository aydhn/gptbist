"""Block I success checklist (pure, tolerant of missing keys; missing => False). Research only; no real order is sent.

Input = one ``run_all_daily`` row (after ``relabel_with_snapshot``). The CandidateGate / robustness thresholds are NOT
touched here; this only summarises, per row, whether every extra Block I evidence item is positive.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

PRIMARY = "placeholder_commission"
ADV_THRESHOLD = 5e7

ITEMS = ("robust_candidate", "global_dsr", "adv_liquid_trimmed_positive", "survivorship_retained",
         "entry_delay_positive", "subperiod_positive")

_MSG = {
    "robust_candidate": "Dayanikli kapi (robust gate) kararı relabel sonrasi CANDIDATE degil.",
    "global_dsr": "Global DSR (dondurulmus havuz) gecmedi veya hesaplanamadi.",
    "adv_liquid_trimmed_positive": "ADV>=5e7 kosusu yok ya da kirpilmis (trim) net asiri getiri pozitif degil.",
    "survivorship_retained": "Hayatta kalma duyarliligi: korunan oran(lar) > 0 degil veya eksik.",
    "entry_delay_positive": "Giris gecikmesi (t+1 kapanis) sonrasi net asiri getiri pozitif degil.",
    "subperiod_positive": "Takvim yili istikrari (alt donem) pozitif degil veya eksik.",
}


def _num(x: Any) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if v == v and abs(v) != float("inf") else None


def _d(x: Any) -> dict:
    return x if isinstance(x, dict) else {}


def evaluate_block_i_success(report_row: Optional[dict]) -> Dict[str, Any]:
    row = _d(report_row)
    det = _d(row.get("robust_detail"))
    out: Dict[str, Any] = {}

    out["robust_candidate"] = _d(row.get("verdicts")).get(PRIMARY) == "CANDIDATE"

    g = _d(row.get("global_dsr"))
    out["global_dsr"] = g.get("passes") is True

    adv = _num(row.get("min_adv"))
    trim = _num(_d(det.get("trim_top_events")).get("mean_after_bps"))
    out["adv_liquid_trimmed_positive"] = bool(adv is not None and adv >= ADV_THRESHOLD and trim is not None
                                              and trim > 0)

    sv = _d(row.get("survivorship"))
    aw, ex = _num(sv.get("retained_fraction_age_weighted")), _num(sv.get("retained_fraction_excl_recent"))
    out["survivorship_retained"] = bool(aw is not None and ex is not None and aw > 0 and ex > 0)

    ed = _num(_d(row.get("entry_delay")).get("net_excess_mean_bps"))
    out["entry_delay_positive"] = bool(ed is not None and ed > 0)

    ys = _d(det.get("year_stability"))
    tot = _num(ys.get("total_excess"))
    out["subperiod_positive"] = bool(ys.get("pass") is True and tot is not None and tot > 0)

    out["overall"] = all(out[k] for k in ITEMS)
    out["explanations_tr"] = {k: _MSG[k] for k in ITEMS if not out[k]}
    return out
