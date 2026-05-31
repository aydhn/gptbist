# Research Monitoring and Champion/Challenger

## Overview
Phase 96 introduced the Research Monitoring and Champion/Challenger layer. This provides offline, deterministic tracking of strategy, model, feature, and calibration health over time.

It answers questions like:
- Is performance decaying?
- Is calibration still reliable?
- Is there feature or model drift?
- Should we promote a challenger?

## Architecture
The system consists of:
- **Models**: Defines snapshots, decay findings, alerts, and watchlist items.
- **Metrics**: Calculates win rate, expectancy, drawdown, etc.
- **Collectors**: Gathers outcomes from backtests, registries, and ledgers.
- **Decay Detector**: Identifies degradation from baselines.
- **Champion/Challenger**: Compares two entities for potential research promotion.
- **Health Engine**: Aggregates metrics and decay into a Health Score (0-100).
- **Alert Router & Escalation**: Generates review cases and routes metadata without triggering real trades.

## Safety Guidelines
- This module generates research metadata, NOT investment advice.
- No real orders are sent.
- Notifications explicitly disclaim their research-only nature.
- No external/paid APIs, cloud LLMs, or web scraping.

## Integrations
Integrates fully with Strategy Registry, Model Registry, Feature Store, Calibration, Portfolio Ledger, and the CLI.
