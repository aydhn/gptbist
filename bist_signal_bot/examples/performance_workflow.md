# Performance Workflow Example

```bash
# Profile a module
python -m bist_signal_bot performance profile --module feature_store

# Run benchmarks
python -m bist_signal_bot performance benchmark --scenario ORCHESTRATOR_DRY_RUN --json

# View cache
python -m bist_signal_bot performance cache list --namespace feature_store

# Check bottlenecks
python -m bist_signal_bot performance bottlenecks

# Generate full performance report
python -m bist_signal_bot performance report
```
