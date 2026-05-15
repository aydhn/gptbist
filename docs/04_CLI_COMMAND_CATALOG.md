# CLI Command Catalog

Bu proje araştırma, backtest, sinyal adayı üretimi ve paper simulation amaçlıdır. Yatırım tavsiyesi değildir. Gerçek emir göndermez.

| Command | Module | Description | Risk Level | Writes Files | Sends Telegram | Requires Confirm | No Real Order Sent | Example |
|---|---|---|---|---|---|---|---|---|
| `healthcheck` | healthcheck | Runs healthcheck | SAFE | False | False | False | True | `python -m bist_signal_bot healthcheck` |
| `runtime loop` | runtime | Runs the runtime orchestrator loop | LONG_RUNNING | True | True | False | True | `python -m bist_signal_bot runtime loop --max-iterations 5` |
| `security kill-switch deactivate` | security | Deactivates the kill-switch | DESTRUCTIVE_REQUIRES_CONFIRM | True | False | True | True | `python -m bist_signal_bot security kill-switch deactivate --confirm` |
| `paper reset` | paper | Resets the paper trading ledger | DESTRUCTIVE_REQUIRES_CONFIRM | True | False | True | True | `python -m bist_signal_bot paper reset --confirm` |
