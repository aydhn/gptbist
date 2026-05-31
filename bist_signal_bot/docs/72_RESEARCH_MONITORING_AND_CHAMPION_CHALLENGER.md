# Research Monitoring and Champion/Challenger V1
## Architecture
- Local-first, JSONL based monitoring
- Research-only: No real trading orders or signals
## Components
- Monitoring Object Types: STRATEGY, MODEL, FEATURE_SET etc.
- Metrics: Win rate, Expectancy, Profit Factor, Drawdown, Calibration Reliability
- Decay Detection: Detects drops below dynamic or static thresholds
- Champion/Challenger Logic: Safe comparison metadata.
- Alerts and escalation: Generates internal alerts, escalates to Review Workflow
- Watchlist: Tracks degraded objects
## Integrations
- Strategy Registry
- Model Registry
- Feature Store
- Review Workflow
- QA / Ops
## Safe Language
- Output must explicitly declare it is for research-only and not financial advice.
## Troubleshooting
- If alerts appear stuck, clear the watchlist via CLI.
