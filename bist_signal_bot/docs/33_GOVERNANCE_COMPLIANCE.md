# Phase 61: Governance & Compliance

BIST Signal Bot includes a local-first Governance & Compliance layer that enforces a strictly research-only operating model. This layer guarantees that no real market orders are sent, no paid APIs are forced, and no investment advice is produced.

## Core Tenets

- **Research-Only**: The bot does not emit real trading instructions.
- **No Real Orders**: Execution is completely disabled or mocked.
- **No Broker API**: Direct connection to brokerage platforms is strictly prohibited.
- **No HTML Scraping**: Uses standardized local data ingestion or permitted public APIs without web scraping.
- **No Paid Services**: Free, open-source models are sufficient for local evaluation.
- **Secret Hygiene**: All output logs, reports, and evidence packs are scrubbed of API keys, tokens, or sensitive credentials.
- **Not Investment Advice**: All output explicitly includes a disclaimer to prevent misinterpretation as financial advice.

## Gates and Policies

The Governance layer provides Gates for different lifecycle stages:
- **Runtime Gate**: Checked before a scan or backtest to ensure execution is safe.
- **Release Gate**: Checked before building a release to verify readiness.
- **Maintenance Gate**: Enforces safety and confirmation for backups/restores/cleanups.
- **Research Lab Gate**: Checks scheduled batch jobs for forbidden commands.

If a gate fails a Critical or High blocking rule, the operation is **BLOCKED**.

## Evidence Packs & Attestation

Governance produces "Evidence Packs"—safe collections of logs, policies, and ledger entries—useful for compliance audits. These packs explicitly exclude sensitive configuration files (`.env`). The layer can also generate a Compliance Attestation summarizing the bot's status against the Governance Policy.

> **Disclaimer:** Governance outputs are operational metrics only. They do not constitute legal or regulatory certification.
