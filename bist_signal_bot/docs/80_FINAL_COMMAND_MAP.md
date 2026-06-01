# Phase 100: Final Command Map

The following core command groups define the primary operator boundaries of the BIST Signal Bot.

**Disclaimer:** Command map entries are local software usage guidance only. They do not constitute investment advice or trading instructions.

## Core Commands

### Setup & Discovery
- `bootstrap`: Initializes local MVP packaging, demo profiles, and onboarding routines.
- `healthcheck`: Aggregates the operational status of all major modules.
- `doctor`: Diagnoses offline configuration, storage, and data issues.

### Maintenance & Quality
- `qa`: Runs release gates and reproducibility checks.
- `ops`: Manages reliability, backups, and readiness.
- `final-audit`: Runs the Go/No-Go release governance checks.
- `final-handoff`: Builds and exports final MVP handoff artifacts.

### Data & Intelligence
- `data-catalog`: Validates dataset schemas, quality, and drift.
- `feature-store`: Serves deterministic offline ML features and checks for leakage.
- `model-registry`: Manages model cards, calibration, and governance statuses.

### Research & Operations
- `orchestrator`: Executes offline research campaigns (DAG-based tasks).
- `monitoring`: Tracks execution metrics and champion vs. challenger models.
- `leaderboard`: Ranks strategies and portfolios based on benchmark cohorts.
- `reports`: Aggregates cross-system diagnostics into daily or weekly markdown files.
