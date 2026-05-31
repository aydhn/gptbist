# 73_RESEARCH_LEADERBOARD_AND_SELECTION.md

## Mimari
The Research Leaderboard subsystem acts as a centralized local evaluation matrix for comparing strategies, ML models, feature sets, and portfolio candidates. It operates entirely offline without making network requests.

## Candidate Types
- STRATEGY
- MODEL
- FEATURE_SET
- SIGNAL_FAMILY
- PORTFOLIO_RESEARCH
- CUSTOM

## Benchmark Cohorts
Cohorts group candidates for direct comparison based on predefined criteria, avoiding arbitrary strategy vs model comparisons unless explicitly mixed.

## Metric Collection
Metrics are collected locally from Backtests, Validation runs, Calibration outcomes, Feature Store, Model Registry, and Monitoring health checks.

## Scoring and Penalties
Scores are computed based on weighted metrics clamped between 0-100.
Penalties are heavily enforced for:
- Leakage (can block)
- Stale Data
- Low Sample Count
- Governance Failures

## Ranking Logic
Deterministic sorting based on scores with fallback hash matching to ensure consistent tie-breakers.

## Selection Policy
Policies dictate minimum score, minimum samples, and block rules (e.g. `strategy_research_selection_v1`).

## Integration
- **Strategy/Model/Feature Store**: Read metrics to compute score.
- **Monitoring/Portfolio**: Feeds into and out of leaderboard metadata.
- **QA/Ops**: Check staleness and blocked candidate inclusion.

## Güvenli Dil Kuralları (Safe Language)
Never output: "trade ready", "best buy", "hedef fiyat", "deploy now". Everything is research-only. No real orders.

## Troubleshooting
Check logs and metrics availability in standard JSONL stores. Use `doctor --leaderboard` for diagnosis.
