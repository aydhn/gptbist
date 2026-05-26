# Command Examples

Deployment commands:
- `python -m bist_signal_bot deploy profiles`
- `python -m bist_signal_bot deploy doctor`
- `python -m bist_signal_bot deploy init-dirs --dry-run`
- `python -m bist_signal_bot deploy env-template --profile RESEARCH_ONLY`
- `python -m bist_signal_bot deploy first-run --dry-run`
- `python -m bist_signal_bot deploy smoke-test`
- `python -m bist_signal_bot deploy runbook`
- `python -m bist_signal_bot deploy platform-commands`
- `python -m bist_signal_bot deploy latest`

### Portfolio Construction (Phase 76)
```bash
python -m bist_signal_bot portfolio-construct build --symbols ASELS THYAO GARAN --method HYBRID
python -m bist_signal_bot portfolio-construct compare --methods EQUAL_WEIGHT SCORE_WEIGHTED HYBRID
python -m bist_signal_bot portfolio-construct rebalance --latest
python -m bist_signal_bot portfolio-construct report --latest --json
```
