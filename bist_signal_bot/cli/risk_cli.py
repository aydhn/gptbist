"""`risk` CLI: daily-loss guard status/reset/simulation. Research/paper only."""

import argparse
import tempfile
from datetime import datetime
from pathlib import Path

from bist_signal_bot.config.settings import get_settings
from bist_signal_bot.intraday.sessions import IST

NO_ORDER = "No real order sent."


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="risk", description="Risk guard (local, research only).")
    sub = p.add_subparsers(dest="risk_command", required=True)
    sub.add_parser("status", help="Show guard state and kill switch")
    r = sub.add_parser("reset", help="Reset the guard (requires --confirm)")
    r.add_argument("--confirm", action="store_true")
    sub.add_parser("simulate-day", help="Synthetic losing day on a temp state path (real state untouched)")
    return p


def _simulate(settings) -> int:
    from bist_signal_bot.risk.daily_loss import DailyLossGuard

    class _MemKS:  # never touches the real kill switch
        def __init__(self):
            self.active = False

        def is_active(self, scope=None):
            return self.active

        def activate(self, scopes, reason, activated_by="x"):
            self.active = True

        def load_state(self):
            return None

        def deactivate(self, confirm=False):
            self.active = False

    class _NoAudit:
        def log_event(self, e):
            pass

    with tempfile.TemporaryDirectory() as td:
        t = datetime(2026, 3, 2, 10, 30, tzinfo=IST)  # a Monday
        g = DailyLossGuard(settings, state_path=Path(td) / "sim.json", clock=lambda: t,
                           kill_switch=_MemKS(), audit=_NoAudit())
        eq0, realized = 100_000.0, 0.0
        g.update(eq0, 0.0, t)
        print(f"start equity {eq0:,.0f}; limit -{g.max_daily_loss_pct}% daily, "
              f"{g.max_consecutive} consecutive losses")
        for i in range(1, 40):
            realized -= 400.0
            snap = g.update(eq0 + realized, realized, t)
            ok, why = g.can_open_new_position(t)
            print(f"loss #{i}: equity={snap['equity']:,.0f} streak={snap['consecutive_losses']} "
                  f"state={snap['state']} new_entries={'ok' if ok else 'BLOCKED'}")
            if not ok:
                print(f"TRIPPED: {why}")
                break
    print(NO_ORDER)
    return 0


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    if args.risk_command == "simulate-day":
        return _simulate(settings)
    from bist_signal_bot.risk.daily_loss import DailyLossGuard
    g = DailyLossGuard(settings)
    if args.risk_command == "reset":
        if not args.confirm:
            print("Refusing to reset without --confirm.")
            print(NO_ORDER)
            return 2
        g.reset(confirm=True)
        print("Guard reset to ACTIVE.")
    s = g.snapshot()
    print(f"guard state={s['state']} day={s['day']} trip={s['trip_kind']} reason={s['trip_reason']}")
    print(f"start_equity={s['start_equity']} equity={s['equity']} peak={s['peak_equity']} "
          f"consecutive_losses={s['consecutive_losses']}")
    try:
        from bist_signal_bot.security.kill_switch import KillSwitchManager
        from bist_signal_bot.storage.paths import get_data_dir
        ks = KillSwitchManager(settings, get_data_dir(settings)).status()
        print(f"kill_switch enabled={ks['enabled']} scopes={ks['scopes']} by={ks['activated_by']} reason={ks['reason']}")
    except Exception as e:
        print(f"kill_switch unavailable: {e}")
    print(NO_ORDER)
    return 0
