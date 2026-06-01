# Operator Playbook

Guidance for operating the BIST Signal Bot MVP locally.

## Daily Routine

- `python -m bist_signal_bot healthcheck --ops --bootstrap --data-catalog`
- `python -m bist_signal_bot ops status`
- `python -m bist_signal_bot reports daily --dry-run --include-ops --include-data-catalog`

## Weekly Routine

- `python -m bist_signal_bot qa release-gate --include-final-audit`
- `python -m bist_signal_bot orchestrator run --campaign QUICK_RESEARCH_SCAN --dry-run`
- `python -m bist_signal_bot monitoring status`
- `python -m bist_signal_bot leaderboard report`

## Monthly Routine

- `python -m bist_signal_bot final-audit run`
- `python -m bist_signal_bot docs-hub coverage`
- `python -m bist_signal_bot feature-store drift --set scanner_core_v1 --json`
- `python -m bist_signal_bot model-registry report`

## Emergency Checks

- `python -m bist_signal_bot ops incident list`
- `python -m bist_signal_bot doctor --all`

## Troubleshooting Route

Check `data-catalog` and `yfinance` adapter logs for stale data issues.

## Safe Commands

All commands are safe to run as long as they are executed without destructive flags unless intended.
