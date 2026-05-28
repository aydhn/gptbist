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

### What-If Scenario Lab
```bash
python -m bist_signal_bot what-if run --source latest-portfolio-construction
python -m bist_signal_bot what-if compare --latest
python -m bist_signal_bot what-if sensitivity --assumption COMMISSION_BPS --source latest-portfolio-construction
python -m bist_signal_bot what-if capital-scale --notionals 50000 100000 250000
python -m bist_signal_bot what-if policy --preset conservative-liquidity
python -m bist_signal_bot what-if report --latest
```

## Event Calendar Examples

```bash
# Import events
python -m bist_signal_bot event-calendar import --file data/imports/events.csv --dry-run
python -m bist_signal_bot event-calendar import --file data/imports/events.csv --confirm

# List events
python -m bist_signal_bot event-calendar list
python -m bist_signal_bot event-calendar list --symbol ASELS
python -m bist_signal_bot event-calendar list --type EARNINGS --json

# Show details
python -m bist_signal_bot event-calendar show EVENT_ID
python -m bist_signal_bot event-calendar show EVENT_ID --json

# Upcoming
python -m bist_signal_bot event-calendar upcoming --days 30
python -m bist_signal_bot event-calendar upcoming --symbol ASELS --json

# Active Windows
python -m bist_signal_bot event-calendar windows
python -m bist_signal_bot event-calendar windows --symbol ASELS --json

# Risk Check
python -m bist_signal_bot event-calendar check ASELS
python -m bist_signal_bot event-calendar check ASELS --strategy moving_average_trend --json

# Portfolio Check
python -m bist_signal_bot event-calendar portfolio-check --symbols ASELS THYAO GARAN
python -m bist_signal_bot event-calendar portfolio-check --portfolio-id PORTFOLIO_ID --json

# Policies
python -m bist_signal_bot event-calendar policies
python -m bist_signal_bot event-calendar policies --json

# Snapshot
python -m bist_signal_bot event-calendar snapshot
python -m bist_signal_bot event-calendar snapshot --json

# Report
python -m bist_signal_bot event-calendar report
python -m bist_signal_bot event-calendar report --latest --json

# Recent
python -m bist_signal_bot event-calendar recent
python -m bist_signal_bot event-calendar recent --limit 10 --json

# Config
python -m bist_signal_bot event-calendar config
```

## Valuation Intelligence
`python -m bist_signal_bot valuation compute ASELS --save`
`python -m bist_signal_bot valuation risk ASELS --json`

## Factors
```bash
python -m bist_signal_bot factors compute ASELS
```

### Market Breadth & Index Internals
```bash
python -m bist_signal_bot breadth compute
python -m bist_signal_bot breadth compute --symbols ASELS THYAO GARAN
python -m bist_signal_bot breadth compute --save --json
python -m bist_signal_bot breadth show
python -m bist_signal_bot breadth show --json
python -m bist_signal_bot breadth advance-decline
python -m bist_signal_bot breadth advance-decline --json
python -m bist_signal_bot breadth participation
python -m bist_signal_bot breadth participation --json
python -m bist_signal_bot breadth high-low
python -m bist_signal_bot breadth high-low --json
python -m bist_signal_bot breadth volume
python -m bist_signal_bot breadth volume --json
python -m bist_signal_bot breadth sector
python -m bist_signal_bot breadth sector --sector BANKACILIK --json
python -m bist_signal_bot breadth divergence
python -m bist_signal_bot breadth divergence --json
python -m bist_signal_bot breadth regime
python -m bist_signal_bot breadth regime --json
python -m bist_signal_bot breadth report
python -m bist_signal_bot breadth report --latest --json
python -m bist_signal_bot breadth recent
python -m bist_signal_bot breadth recent --limit 10 --json
python -m bist_signal_bot breadth config
python -m bist_signal_bot scan symbols ASELS THYAO --source local_file --strategy moving_average_trend --breadth-context
python -m bist_signal_bot portfolio-construct build --symbols ASELS THYAO GARAN --method HYBRID --breadth-aware
python -m bist_signal_bot review show ITEM_ID --breadth
python -m bist_signal_bot explain card --symbol ASELS --strategy moving_average_trend --include-breadth
```
