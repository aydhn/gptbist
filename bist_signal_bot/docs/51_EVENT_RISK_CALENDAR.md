# Event Risk Calendar

The Event Risk Calendar provides local-first tracking for financial results, macro indicators, corporate actions, and dividend windows.

## Features
- **Local Event Calendar**: Tracks BIST events using local CSV/JSON without web scraping or external APIs.
- **Blackout Policies**: Configurable policies that identify high-risk event windows.
- **Event Risk Engine**: Assess signals and portfolios for concentration risk and blackout collisions.
- **Event Risk Decision**: Assigns non-binding research tags (ALLOW, WARN, REQUIRE_REVIEW, RESEARCH_BLOCK).

## Security & Principles
- No web scraping (HTML, Playwright, Selenium are forbidden).
- No broker APIs.
- No real orders are generated.
- All operations are research-only and do not guarantee future price direction.
