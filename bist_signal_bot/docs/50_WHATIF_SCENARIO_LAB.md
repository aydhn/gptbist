# What-If Scenario Lab

The What-If Scenario Lab provides an offline, local-first research environment for counterfactual simulation. It does not send any real orders, connect to broker APIs, or use OpenAI APIs.

## Purpose
The purpose is to answer "what-if" questions about the portfolio or strategy.
- What if commissions were doubled?
- What if slippage increased by 50%?
- What if we used a 500,000 TRY notional instead of 100,000 TRY?
- What if we enforced a strict liquidity filter?

## Default Scenarios
The `WhatIfScenarioFactory` automatically provides several default scenarios including:
- Baseline
- Cost +50% and +100%
- Slippage +50% and +100%
- Liquidity stress
- Portfolio scale (50k, 100k, 500k)
- Constraint overrides (Max positions, Threshold changes, Sector weights)
- Calibration, Scorecard, and Monte Carlo toggles.

## Assumption Overrides
Overriding assumptions builds a local context that gets evaluated by the `CounterfactualEngine` through `PortfolioConstructionEngine` without altering the global static `Settings`. Unsafe or broker-related overrides are explicitly blocked and cause warnings.

## Capital Scaling & Policy Sandbox
- **Capital Scaling**: Scales the `portfolio_notional` through multiple scenarios to detect liquidity breakpoints and calculate the cost curve.
- **Policy Sandbox**: Applies presets representing a set of overrides (like conservative liquidity constraints) without changing the live configurations.

## Architecture
The CLI triggers the `WhatIfEngine`, which loops over the requested scenarios via the `CounterfactualEngine`. The metrics are analyzed by `WhatIfComparisonEngine` and `SensitivityAnalyzer` to rank scenarios and find sensitive variables. Finally, reports are saved through `WhatIfStore` and potentially attached to Analyst Reviews via `ReviewEvidenceCollector` and `EvidenceCard`.

## Safety Guidelines
All results are research-only and should include the following disclaimer:
"What-if scenario is research-only. It is not investment advice or an order instruction. No real order was sent."
