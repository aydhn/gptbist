"""Manual one-shot daily model cycle: due? -> train challenger -> drift -> report -> (--confirm only) promote.

Research/paper only. Manually invoked (no scheduler). A challenger whose gate verdict is not CANDIDATE is only
reported, never promoted. Promotion happens only with confirm=True AND ``ModelLifecycle.promote`` agreeing (gate
CANDIDATE + better than champion + kill switch + preflight + audit). ``dry_run`` changes no state at all.
No real order is ever sent.
"""
from __future__ import annotations

from typing import Callable, Optional

from bist_signal_bot.model_loop.daily_lifecycle import DEFAULT_RETRAIN_DAYS, due_for_retrain

NO_ORDER = "No real order sent."


def run_daily_cycle(registry, lifecycle, as_of, only_if_due: bool = False, retrain_days: int = DEFAULT_RETRAIN_DAYS,
                    dry_run: bool = False, confirm: bool = False,
                    out: Optional[Callable[[str], None]] = None) -> dict:
    lines: list = []

    def say(msg: str) -> None:
        lines.append(f"{msg} {NO_ORDER}")
        if out is not None:
            out(lines[-1])

    res: dict = {"as_of": str(as_of), "due": None, "trained": False, "challenger_id": None, "promotion": None,
                 "mode": "DRY_RUN" if dry_run else ("CONFIRM" if confirm else "TRAIN_NO_PROMOTE"), "no_real_order_sent": True,
                 "lines": lines}
    due, why = due_for_retrain(registry, as_of, retrain_days)
    res["due"] = due
    say(f"[1/5] retrain schedule: due={due} ({why})")
    if only_if_due and not due:
        res["status"] = "NOOP_NOT_DUE"
        say("not due: nothing to do.")
        return res
    if dry_run:
        res["status"] = "DRY_RUN"
        say("dry-run: would train a challenger, evaluate drift and report; no state changed, nothing promoted.")
        return res

    rep = lifecycle.evaluate(as_of, force=True)  # manual cycle: train regardless of drift; kill switch/min-days still apply
    res["trained"], res["challenger_id"] = bool(rep.trained), rep.challenger_id
    if rep.drift is not None:
        res["drift"] = {"severity": rep.drift.severity, "reasons": list(rep.drift.reasons)}
        say(f"[3/5] drift: severity={rep.drift.severity} reasons={rep.drift.reasons}")
    if not rep.trained:
        res["status"] = "NO_CHALLENGER"
        say(f"[2/5] no challenger trained: {rep.skipped_reason}")
        return res
    if not confirm:
        say("challenger kaydedildi; terfi yok (--confirm verilmedi).")
    cmp_ = rep.comparison or {}
    verdict = cmp_.get("gate_verdict")
    say(f"[2/5] challenger {rep.challenger_id} trained: gate_verdict={verdict} (never auto-champion)")
    if verdict != "CANDIDATE":
        res["status"] = "REPORT_ONLY"
        say(f"[4/5] gate_verdict={verdict}: report only, challenger can never become champion.")
        return res
    say(f"[4/5] gate CANDIDATE: better_than_champion={cmp_.get('better')} reasons={cmp_.get('reasons')}")
    pr = lifecycle.promote(rep.challenger_id, confirm=bool(confirm))
    res["promotion"] = {"status": pr.status, "dry_run": pr.dry_run, "reasons": list(pr.reasons)}
    res["status"] = pr.status
    say(f"[5/5] promote: {pr.status} dry_run={pr.dry_run} reasons={pr.reasons}")
    return res
