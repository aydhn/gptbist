# Command Examples
python -m bist_signal_bot breadth snapshot --symbols ASELS THYAO GARAN

# Research Lab
python -m bist_signal_bot lab plan daily --symbols ASELS THYAO GARAN
python -m bist_signal_bot lab enqueue --job BACKTEST --symbol ASELS --strategy moving_average_trend
python -m bist_signal_bot lab run --next

## Telegram Command Center Examples

```bash
# Check configuration
python -m bist_signal_bot telegram-center config

# Simulate a command locally (Dry Run)
python -m bist_signal_bot telegram-center dry-run "/status"
python -m bist_signal_bot telegram-center dry-run "/kb ASELS momentum breadth zayıf" --json

# Route a command
python -m bist_signal_bot telegram-center route "/health" --chat-id TEST_CHAT --dry-run

# Manage the notification inbox
python -m bist_signal_bot telegram-center inbox
python -m bist_signal_bot telegram-center inbox --status FAILED

# Generate a digest
python -m bist_signal_bot telegram-center digest daily
python -m bist_signal_bot telegram-center digest runtime --dry-run
```
