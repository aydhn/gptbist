# Operator Daily Routine Example

This is a simulated example of what an operator running the bot locally might execute daily.

### Morning Check

1. Confirm basic system health across all features:
```bash
python -m bist_signal_bot healthcheck --ops --bootstrap --data-catalog --final-handoff
```

2. Confirm there are no systemic data issues or stale caches:
```bash
python -m bist_signal_bot doctor --full
```

3. Generate the daily aggregated report:
```bash
python -m bist_signal_bot reports daily --dry-run --include-ops --include-data-catalog
```

### End of Day Routine

1. Sync local backups to prevent data loss:
```bash
python -m bist_signal_bot ops backup --sync
```

2. Perform readiness checks for the next morning:
```bash
python -m bist_signal_bot ops readiness --include-final-handoff
```
