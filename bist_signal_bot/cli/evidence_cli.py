"""`evidence` CLI: point-in-time paper replay and paper-vs-backtest divergence. Research only; no real order sent."""

import argparse

from bist_signal_bot.config.settings import get_settings

NO_ORDER = "No real order sent."


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="evidence", description="Measured paper/backtest evidence (local data only).")
    sub = p.add_subparsers(dest="evidence_command", required=True)
    for name, h in (("replay", "Replay the paper engine day by day (point-in-time)"),
                    ("compare", "Compare paper replay vs backtest and write a divergence report")):
        s = sub.add_parser(name, help=h)
        s.add_argument("--strategy", default="moving_average_trend")
        s.add_argument("--days", type=int, default=250, help="last N trading days present in the data")
        s.add_argument("--symbols", nargs="*", default=None, help="default: every symbol with local daily data")
        s.add_argument("--decision-layer", action="store_true")
        s.add_argument("--use-risk", action="store_true", help="enable trade/portfolio risk engines in paper")
        s.add_argument("--execution-mode", default="LATEST_CLOSE_RESEARCH",
                       choices=["LATEST_CLOSE_RESEARCH", "NEXT_OPEN_SIMULATED", "NEXT_CLOSE_SIMULATED"])
    return p


def _universe_and_window(settings, symbols, days):
    from bist_signal_bot.data.symbol_universe import DEFAULT_SEED_SYMBOLS
    from bist_signal_bot.evidence.replay import load_local_frames, trading_dates
    import datetime as _dt

    cand = symbols or [str(getattr(s, "symbol", s)).upper() for s in DEFAULT_SEED_SYMBOLS]
    # include any other symbol with local daily data when none were given
    if not symbols:
        try:
            from bist_signal_bot.storage.local_store import LocalMarketDataStore
            from bist_signal_bot.data.models import Timeframe
            cand = sorted(set(cand) | {s.upper() for s in LocalMarketDataStore(settings=settings).list_available_symbols("yfinance", Timeframe.DAILY)})
        except Exception:
            pass
    frames = load_local_frames(settings, cand)
    all_days = trading_dates(frames, _dt.date(1990, 1, 1), _dt.date(2100, 1, 1))
    sel = all_days[-days:]
    return frames, (sel[0] if sel else None), (sel[-1] if sel else None)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    frames, start, end = _universe_and_window(settings, [s.upper() for s in (args.symbols or [])], args.days)
    if not frames or start is None:
        print(f"No local daily data found. {NO_ORDER}")
        return 1
    symbols = sorted(frames)
    from bist_signal_bot.paper.models import PaperExecutionMode
    mode = PaperExecutionMode(args.execution_mode)

    if args.evidence_command == "replay":
        from bist_signal_bot.evidence.replay import replay_paper
        r = replay_paper(args.strategy, symbols, start, end, settings=settings, use_decision_layer=args.decision_layer,
                         execution_mode=mode, frames=frames, use_trade_risk=args.use_risk, use_portfolio_risk=args.use_risk,
                         close_open_at_end=True)
        print(f"Paper replay {args.strategy}  {start}..{end}  symbols={len(symbols)}  days={r.days}")
        for k, v in r.summary().items():
            print(f"  {k:<16}{v}")
        if r.rejections:
            print(f"  rejection sample: {r.rejections[0]}")
        for m in r.issues[:3]:
            print(f"  issue: {m}")
        return 0

    from bist_signal_bot.evidence.compare import compare_paper_backtest
    rpt = compare_paper_backtest(args.strategy, symbols, start, end, settings=settings, use_risk=args.use_risk,
                                 use_decision_layer=args.decision_layer, execution_mode=mode, frames=frames)
    f = lambda x, n=2: "n/a" if x is None else f"{x:.{n}f}"
    print(f"Divergence {rpt.strategy}  {rpt.start}..{rpt.end}  symbols={len(rpt.symbols)}  "
          f"paper={rpt.paper_execution_mode} backtest={rpt.backtest_execution_mode} risk={'on' if rpt.use_risk else 'off'}")
    if rpt.insufficient_trades:
        print("  insufficient trades for a meaningful comparison")
    print(f"  {'metric':<26}{'paper':>12}{'backtest':>12}{'diff':>12}")
    print(f"  {'trades':<26}{rpt.paper_trades:>12}{rpt.backtest_trades:>12}{('matched ' + str(rpt.matched_trades)):>12}")
    print(f"  {'total return %':<26}{f(rpt.paper_total_return_pct):>12}{f(rpt.backtest_total_return_pct):>12}{f(rpt.return_diff_pct_points):>12}")
    print(f"  {'total cost':<26}{f(rpt.paper_total_cost):>12}{f(rpt.backtest_total_cost):>12}{f(rpt.cost_diff):>12}")
    print(f"  {'max drawdown %':<26}{f(rpt.paper_max_drawdown_pct):>12}{f(rpt.backtest_max_drawdown_pct):>12}{f(rpt.drawdown_diff_pct_points):>12}")
    print(f"  entry aligned {f(rpt.entry_date_aligned_pct, 1)}%  exit aligned {f(rpt.exit_date_aligned_pct, 1)}%  "
          f"fill diff bps entry {f(rpt.entry_fill_diff_bps_mean_abs)} exit {f(rpt.exit_fill_diff_bps_mean_abs)} (abs mean)")
    print(f"  tracking error {f(rpt.tracking_error_annualized_pct)}% ann.  max equity divergence {f(rpt.max_equity_divergence)} "
          f"({f(rpt.max_equity_divergence_pct_of_capital)}% of capital)")
    for a in rpt.attribution:
        print(f"  cause: {a}")
    print(f"  report: {rpt.json_path}")
    print(rpt.disclaimer)
    return 0
