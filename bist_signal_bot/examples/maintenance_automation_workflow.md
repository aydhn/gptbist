# Maintenance Automation Example Workflow

```bash
# 1. View default cadence policies
python -m bist_signal_bot maintenance-auto policies --cadence WEEKLY --json

# 2. Dry-run a daily maintenance plan to see what would happen
python -m bist_signal_bot maintenance-auto plan --cadence DAILY --dry-run

# 3. Execute a monthly maintenance run safely
python -m bist_signal_bot maintenance-auto run --cadence MONTHLY --dry-run --save --json

# 4. Check for cleanup candidates (dry-run)
python -m bist_signal_bot maintenance-auto cleanup --artifact-kind CACHE --dry-run --json

# 5. Generate a Backup Manifest
python -m bist_signal_bot maintenance-auto backup --manifest-only --json

# 6. Verify stale reports or failed jobs
python -m bist_signal_bot maintenance-auto staleness --json
```
