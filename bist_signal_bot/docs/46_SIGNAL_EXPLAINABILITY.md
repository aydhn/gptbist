# Signal Explainability (Phase 74)

## Architecture
The explainability layer generates insights into why a signal was triggered.
It produces:
- Feature Attribution
- Indicator States
- Rule Trace
- ML / Ensemble / Risk / Execution explanations
- History Context

## Research-Only
Explainability outputs are metadata. They are NOT investment advice. No broker API is called.

## CLI Usage
`python -m bist_signal_bot explain signal --symbol ASELS`
`python -m bist_signal_bot explain strategy moving_average_trend --symbol ASELS`
