# Developer Guide

## Drift Monitoring
The drift monitoring system (Phase 58) evaluates the degradation of feature distributions, model calibration, signal accuracy, strategy performance, and portfolio exposures over time. It is entirely local and operates offline.

*Disclaimer: Drift monitoring is for research purposes only. It is not investment advice and does not send real market orders.*

## Research Lab Automation (Phase 59)
The Research Lab introduces safe, budgeted queueing capabilities.
It leverages JSONL localized storage to ensure persistent append-only logs for Jobs, Queue, and Batch Runs.
All tasks run in an isolated environment that explicitly mocks or blocks broker API keys, Telegram payloads, and remote network calls.
The queue processor runs offline and deduplicates identical configurations spanning configurable hours to conserve resources.

*Disclaimer: The research automation is purely for analytics. It does not send real market orders, it makes zero network calls to exchanges, and output must not be considered financial advice.*

### Governance & Compliance Katmanı (Phase 61)
BIST Signal Bot strictly operates under a set of governance rules enforced by the Governance layer. Ensure that your modifications do not violate the core tenets:
- No real orders
- No broker APIs
- No HTML scraping
- Proper secret hygiene

See `docs/33_GOVERNANCE_COMPLIANCE.md` for details.

## Knowledge Base
The system incorporates a local embedding and indexing system. See `35_RESEARCH_KNOWLEDGE_BASE.md` for guidelines.
