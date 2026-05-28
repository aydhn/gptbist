# Developer Guide

To contribute to the deployment package:
- See `bist_signal_bot/deployment`
- Safe defaults are enforced in `DeploymentProfile`.
- Use `pytest` for all unit testing.
- No HTML scraping or Paid APIs are allowed.

### Portfolio Construction Layer
The portfolio construction layer (`portfolio_construction/`) operates fully offline. Ensure that testing logic does not attempt to resolve yfinance or remote brokers. Mock the input dataframes and ensure your candidate builder uses the local standard metrics to avoid leaking forward returns into weight optimization.

- **Phase 82 Valuation**: Architecture is inside `bist_signal_bot/valuation`. Pydantic models with extreme caution on NO Target Price predictions.

## Factor Engine
The factor engine is located in `bist_signal_bot/factors`.
