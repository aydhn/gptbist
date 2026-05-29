# Analyst Review Workflow v1

The Analyst Review Workflow provides a human-in-the-loop, research-only layer for reviewing signals, symbols, and portfolios before any simulated action is logged. It incorporates case management, playbook routing, standard checklists, appending decision journals, and governance signoffs.

## Principles
1. **Research Only**: This is NOT a trading approval system. It does not send any real orders to brokers.
2. **Append-Only Journal**: Decision history is tracked immutably. Corrections are new entries.
3. **Deterministic Playbooks**: Playbooks are assigned deterministically based on context conflicts (e.g. `MACRO_PRESSURE`, `EVENT_BLACKOUT`).
4. **Data Isolation**: Workflow storage relies on local files only, operating 100% offline.

## Core Components

- **ReviewCaseBuilder**: Generates a new `ReviewCase` based on a `UnifiedContextSnapshot`.
- **ReviewPlaybookRegistry**: Maintains standard playbooks defining what checklists or signoffs are needed based on risk.
- **ReviewChecklistBuilder**: Dynamically produces a verification checklist for the analyst.
- **ReviewPriorityEngine**: Calculates case priority (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
- **DecisionJournal**: An append-only log of human analyst notes with safety guardrails blocking "trade approved" claims.
- **ReviewSignoffManager**: Handles formal signoffs from required parties (e.g., Lead Analyst).
- **ReviewDataActionQueue**: Captures offline data gaps as trackable tasks for the data layer.
- **ReviewPatternDetector**: Tracks multiple instances of the same failure mode (e.g., same evidence gap missing frequently).

## Storage
Data is persisted in:
- `data/review_workflow/cases/review_cases.jsonl`
- `data/review_workflow/journal/decision_journal.jsonl`
- ...

## Security & Governance
Outputs are subjected to safe-language filtering. Words like "buy approved" or "sell approved" are masked as `[REDACTED_UNSAFE_CLAIM]`. No internet or broker APIs are connected.
