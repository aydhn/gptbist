# Command Examples

Here are common CLI operations you can perform with the BIST Signal Bot.

## Release Readiness

```bash
# Check basic imports and safe configs
python -m bist_signal_bot release check

# Full readiness score and blockers
python -m bist_signal_bot release readiness

# Run safe launch rehearsal (mock scenarios)
python -m bist_signal_bot release rehearse

# Build manifest and release notes
python -m bist_signal_bot release candidate --version 0.1.0 --confirm
```

## Scenario Runner

```bash
# Run the smoke test scenario
python -m bist_signal_bot scenario run smoke

# Run acceptance scenario with golden comparison
python -m bist_signal_bot scenario run acceptance --compare
```

## Data and ML
```bash
# Download data (offline mock by default, configured via settings)
python -m bist_signal_bot data download

# Train basic strategy models
python -m bist_signal_bot ml train
```
