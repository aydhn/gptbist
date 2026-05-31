# Feature Store Workflow Examples

```bash
# List all feature contracts
python -m bist_signal_bot feature-store contracts

# List features
python -m bist_signal_bot feature-store list

# List sets
python -m bist_signal_bot feature-store sets

# Compute feature
python -m bist_signal_bot feature-store compute --symbols ASELS THYAO --set scanner_core_v1

# Serve feature frame for scanner
python -m bist_signal_bot feature-store serve --scanner --symbols ASELS THYAO

# Assess quality
python -m bist_signal_bot feature-store quality --set scanner_core_v1 --symbols ASELS THYAO

# Detect leakage
python -m bist_signal_bot feature-store leakage --set scanner_core_v1 --symbols ASELS THYAO

# Generate report
python -m bist_signal_bot feature-store report
```
