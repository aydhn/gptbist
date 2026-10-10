# Kill Switch Active

Bu proje araştırma, backtest, sinyal adayı üretimi ve paper simulation amaçlıdır. Yatırım tavsiyesi değildir. Gerçek emir göndermez.


## Risk guard (daily loss) tripped the kill switch

`risk/daily_loss.py::DailyLossGuard` engages the PAPER kill switch (`activated_by=risk_daily_loss_guard`) when
the daily loss, consecutive-loss or trailing-drawdown limit is hit (`RISK_MAX_DAILY_LOSS_PCT`,
`RISK_MAX_CONSECUTIVE_LOSSES`, `RISK_MAX_DRAWDOWN_PCT`). New entries are blocked; exits stay allowed.
Daily-loss and consecutive-loss trips auto-reset at the next trading-day open (only if the kill switch was
engaged by the guard). A drawdown trip, or a corrupt `<DATA_DIR>/risk/daily_loss_state.json` (fail closed),
needs `python -m bist_signal_bot risk reset --confirm`. A manually engaged kill switch is never auto-cleared.
Inspect with `python -m bist_signal_bot risk status`. The orchestrator only consults the guard when
`RUNTIME_USE_DECISION_LAYER=True` (default False). No real order sent.

## Forward shadow job behaviour
`forward run-daily` consults the kill switch (scopes ALL, PAPER or SCHEDULER). While it is active: NO new decisions are
written, NO new simulated entries are made (affected baskets are recorded as `blocked`), exits of already-open simulated
baskets and mark-to-market continue (reduce-only, simulation), the run is logged in `data/forward/runs.jsonl` with
status `KILL_SWITCH`, and a toggle raises a `KILL_SWITCH_TOGGLED` alert. A corrupt kill-switch file fails closed.
Days skipped this way are simply missing from the forward record (the basket waits in cash); never backfill them.
Inspect with `python -m bist_signal_bot forward health`. No real order sent.
