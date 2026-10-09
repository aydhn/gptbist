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
