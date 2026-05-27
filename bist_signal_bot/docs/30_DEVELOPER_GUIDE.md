# Developer Guide

To contribute to the deployment package:
- See `bist_signal_bot/deployment`
- Safe defaults are enforced in `DeploymentProfile`.
- Use `pytest` for all unit testing.
- No HTML scraping or Paid APIs are allowed.

### Portfolio Construction Layer
The portfolio construction layer (`portfolio_construction/`) operates fully offline. Ensure that testing logic does not attempt to resolve yfinance or remote brokers. Mock the input dataframes and ensure your candidate builder uses the local standard metrics to avoid leaking forward returns into weight optimization.
\n- Disclosure Intelligence is available for offline narrative risk extraction and digest generation. See 52_DISCLOSURE_INTELLIGENCE.md for details.
