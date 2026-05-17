
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

## Phase 49: End-to-End Scenario Runner

```bash
# List available scenarios
python -m bist_signal_bot scenario list
python -m bist_signal_bot scenario list --json

# Show details of a specific scenario
python -m bist_signal_bot scenario show smoke
python -m bist_signal_bot scenario show acceptance --json

# Run a specific scenario
python -m bist_signal_bot scenario run smoke
python -m bist_signal_bot scenario run acceptance
python -m bist_signal_bot scenario run e2e-research
python -m bist_signal_bot scenario run e2e-ml
python -m bist_signal_bot scenario run security-failsafe
python -m bist_signal_bot scenario run monitoring-recovery
python -m bist_signal_bot scenario run performance-smoke

# Compare or update golden snapshots during run
python -m bist_signal_bot scenario run acceptance --compare-golden
python -m bist_signal_bot scenario run acceptance --update-golden --confirm

# Run all scenarios
python -m bist_signal_bot scenario run-all --type SMOKE
python -m bist_signal_bot scenario run-all --stop-on-failure

# Replay a specific scenario run
python -m bist_signal_bot scenario replay RUN_ID

# Manage Golden Snapshots
python -m bist_signal_bot scenario golden compare acceptance
python -m bist_signal_bot scenario golden update acceptance --confirm

# List recent runs and clean up sandboxes
python -m bist_signal_bot scenario recent
python -m bist_signal_bot scenario cleanup RUN_ID --confirm

# Show scenario configuration
python -m bist_signal_bot scenario config
```
