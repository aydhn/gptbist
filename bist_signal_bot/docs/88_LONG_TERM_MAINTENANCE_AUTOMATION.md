# Long-Term Maintenance Automation (Phase 108)

Provides an offline, local-first architecture for scheduled checks, cleanup jobs, self-audit cadences, and artifact rotation without relying on any external APIs or cloud LLMs.

## Core Features
1. **Cadence Policies**: Define Daily, Weekly, Monthly, and Quarterly maintenance plans.
2. **Maintenance Actions**: Support for Dry-Run by default. Destructive actions require explicit confirm.
3. **Cleanup and Retention**: Rotate logs, clean up local JSONL stores and exports safely.
4. **Backup Manifests**: Local checksums of critical artifacts without relying on broker sync.
5. **Staleness Detection**: Detect failed/abandoned scheduled jobs.

## Safety & Governance
- No real orders are sent.
- Broker and API commands are blocked explicitly during automated maintenance.
- Dry-run applies by default to all tasks unless `--confirm` is passed.
- Output always includes disclaimers stating it is not investment advice or a live trade command.

## CLI Commands
- `python -m bist_signal_bot maintenance-auto policies`
- `python -m bist_signal_bot maintenance-auto plan --cadence DAILY --dry-run`
- `python -m bist_signal_bot maintenance-auto run --cadence WEEKLY --dry-run --save`

## Integrations
Integrates automatically with Ops Readiness, QA Gate, Research Orchestrator, and Final Audit.
