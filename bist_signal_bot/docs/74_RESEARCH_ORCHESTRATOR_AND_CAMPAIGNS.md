# Research Orchestrator and Campaigns (Phase 98)

## Architecture
The Research Orchestrator provides a safe, reproducible, offline execution environment for algorithmic research.
It combines various standalone systems (Data Catalog, Feature Store, Signal Scanner, Backtester, Portfolios, Leaderboard) into a dependency-aware DAG.

## Design Goals
- Single-command research campaign execution.
- Dependency-aware workflow logic (Feature Compute runs before Scanner, etc.)
- Enforces guardrails such as dry-run by default, blocking unsafe terminology, and strictly blocking broker/order commands.
- Local execution output artifacts (Manifests, run traces) for audits.

## Campaign Types
1. **QUICK_RESEARCH_SCAN**: Basic flow, Data Catalog Gate -> Feature Compute -> Scanner -> Context Fusion -> Report
2. **FULL_RESEARCH_PIPELINE**: Deep flow encompassing Backtesting, Model Validation, and Leaderboard.
3. **MODEL_GOVERNANCE_CAMPAIGN**: Specific execution around validating ML models.
4. **QA_OPS_RELEASE_CHECK**: End-to-end check for code releases.

## Tasks and DAG
`ResearchTask` entities build a Directed Acyclic Graph. Cycles are detected and blocked. The `ResearchDAGBuilder` computes a topological sort, making execution linear and deterministic.

## Execution Modes
- **DRY_RUN** (default): Validates tasks but does not execute destructive actions or time-consuming computations.
- **LOCAL_EXECUTE**: Executes normally, saving states offline.
- **REPLAY**: Restores a run manifest for comparison.

## Guardrails
Guardrails actively prevent:
- Unsafe language (e.g. "buy order", "hedef fiyat").
- Broker execution API commands.
- External calls using curl/wget.

## Run Manifest
After execution, a `ResearchRunManifest` captures input parameters, final state checksums, config snapshots, and environment details. This guarantees the traceability of the research.

## Integrations
- **Data Catalog & Feature Store**: Upstream prerequisites. If they block, campaigns move to WATCH/BLOCKED.
- **Model Registry & Monitoring**: Governs which models enter the leaderboard during backtest runs.
- **QA/Ops**: Release gates explicitly check orchestrator capability.

## Disclaimer
All generated reports and manifestations include standard disclaimers highlighting that the outputs are entirely local research data and *not* real financial advice or broker orders.
