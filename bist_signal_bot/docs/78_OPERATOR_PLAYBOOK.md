# Phase 100: Operator Playbook

This playbook provides local software maintenance guidance for the BIST Signal Bot. It establishes standard cadences for ensuring data freshness, model integrity, and system health.

**Disclaimer:** This playbook is local software upkeep guidance only. It is not investment advice, broker operations guidance, or a trading instruction. No real orders are sent.

## Daily Routine

1. **System Healthcheck**
   `python -m bist_signal_bot healthcheck --ops --bootstrap --data-catalog`
2. **Operations Status**
   `python -m bist_signal_bot ops status`
3. **Daily Reports**
   `python -m bist_signal_bot reports daily --dry-run --include-ops --include-data-catalog`

## Weekly Routine

1. **Release Gate Validation**
   `python -m bist_signal_bot qa release-gate --include-final-audit`
2. **Quick Research Scan**
   `python -m bist_signal_bot orchestrator run --campaign QUICK_RESEARCH_SCAN --dry-run`
3. **Monitoring Status**
   `python -m bist_signal_bot monitoring status`

## Monthly Routine

1. **Final Pre-Release Audit**
   `python -m bist_signal_bot final-audit run`
2. **Feature Store Drift Check**
   `python -m bist_signal_bot feature-store drift --set scanner_core_v1 --json`
3. **Model Registry Report**
   `python -m bist_signal_bot model-registry report`

## Emergency Checks

- `python -m bist_signal_bot doctor --full`
- `python -m bist_signal_bot maintenance backup-verify`

## Troubleshooting Routes

- **Data Staleness**: If data fails to import, verify the offline data folder or adapt the offline source providers.
- **Model Drift**: If drift triggers, rebuild the ML dataset offline (`python -m bist_signal_bot ml-dataset build`).
