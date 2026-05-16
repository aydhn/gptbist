
## Phase 48: Reports

```bash
# Generate daily report
python -m bist_signal_bot report daily

# Generate daily report for specific symbols
python -m bist_signal_bot report daily --symbols ASELS THYAO GARAN

# Generate report and output JSON
python -m bist_signal_bot report daily --json

# Generate weekly report
python -m bist_signal_bot report weekly

# Generate runtime report
python -m bist_signal_bot report runtime

# Send digest
python -m bist_signal_bot report send --latest --confirm

# Export html
python -m bist_signal_bot report export --latest --format html

# View config
python -m bist_signal_bot report config
```
