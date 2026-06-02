# Performance Workflow Examples

## Profile a Module
`python -m bist_signal_bot performance profile --module feature_store`

## Benchmark Scenario
`python -m bist_signal_bot performance benchmark --scenario ORCHESTRATOR_DRY_RUN --json`

## Cache
`python -m bist_signal_bot performance cache list`
`python -m bist_signal_bot performance cache invalidate --namespace feature_store --confirm`

## Analysis
`python -m bist_signal_bot performance bottlenecks`
`python -m bist_signal_bot performance regressions`
`python -m bist_signal_bot performance report`
