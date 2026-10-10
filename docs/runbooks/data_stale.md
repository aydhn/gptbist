# Data Stale

Bu proje araştırma, backtest, sinyal adayı üretimi ve paper simulation amaçlıdır. Yatırım tavsiyesi değildir. Gerçek emir göndermez.

## Forward shadow job: stale data
`forward run-daily` computes the expected session (today after 18:30 Istanbul on a trading day, otherwise the previous
trading day, using the BIST holiday calendar) and the newest session reached by >= `FORWARD_MIN_COVERAGE` of symbols.
If the lag exceeds `FORWARD_MAX_LAG_SESSIONS` (default 0) the run finishes with status `STALE`: no decision is written
(fail closed) and a `STALE_DATA` alert is raised when lag > `FORWARD_ALERT_STALE_SESSIONS`. Fix: check network / yfinance
(`python -m bist_signal_bot daily status`), then re-run `forward run-daily` (the 08:30 catch-up does this automatically; a late
fetch is only used for the then-current session, missed days are never backfilled into decisions). No real order sent.
