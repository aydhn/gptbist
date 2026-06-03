# Maintenance Automation Workflow Example

```bash
# 1. Inspect existing policies
python -m bist_signal_bot maintenance-auto policies --cadence WEEKLY --json

# 2. Plan a daily check (defaults to dry-run)
python -m bist_signal_bot maintenance-auto plan --cadence DAILY --dry-run

# 3. Run weekly maintenance checks in dry-run
python -m bist_signal_bot maintenance-auto run --cadence WEEKLY --dry-run --save --json

# 4. Cleanup cache (dry-run)
python -m bist_signal_bot maintenance-auto cleanup --artifact-kind CACHE --dry-run --json

# 5. List retention policies
python -m bist_signal_bot maintenance-auto retention

# 6. Generate a backup manifest
python -m bist_signal_bot maintenance-auto backup --dry-run

# 7. Check for stale reports/caches
python -m bist_signal_bot maintenance-auto staleness

# 8. Get the latest maintenance report
python -m bist_signal_bot maintenance-auto report --latest --json
```
