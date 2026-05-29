# Unified Context Fusion (Phase 86)

## Overview
The Unified Context Fusion layer aggregates research signals, ML scores, risk assessments, execution simulations, calibration, validation, Monte Carlo, strategy registries, event risks, disclosure impacts, financials, valuation, factors, breadth, macro context, portfolio context, and knowledge context into a single local-first **Unified Context Snapshot** and **Research Graph**.

## Features
- **Context Collection**: Aggregates signals from all available offline subsystems.
- **Normalization**: Standardizes scores on a 0-100 scale, adjusting for inverted logic where higher numbers indicate higher risk (e.g. Risk, Macro).
- **Dynamic Weighting**: Redistributes weights deterministically when optional layers are missing.
- **Conflict Resolution**: Detects analytical contradictions such as "High technical score but high risk pressure".
- **Evidence Gap Detection**: Marks missing or stale data that limits research confidence.
- **Research Graph**: Builds a local metadata network connecting symbols, signals, and context layers.
- **Composite Research Score**: Calculates a final blended research score out of 100 to rank scanner candidates.

## CLI Usage
```bash
python -m bist_signal_bot context build --symbol ASELS
python -m bist_signal_bot context show --symbol ASELS
python -m bist_signal_bot context graph --symbol ASELS
python -m bist_signal_bot context conflicts --latest
python -m bist_signal_bot context score --symbol ASELS
python -m bist_signal_bot context report
```

## Security & Compliance
- **No Paid APIs / No Cloud LLMs**: All operations execute locally.
- **No Broker Routing**: Composite scores and context graphs are **research-only**. They do not execute market orders.
- **Unsafe Claim Guards**: Summaries redact guarantees and absolute claims (e.g., "garanti", "kesin", "risksiz").
