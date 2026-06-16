# AGENTS.md

Operating guide for autonomous agents in this repository. The full reference is
[CLAUDE.md](CLAUDE.md) — read it first. This file restates the non-negotiables.

## Golden rules

1. **Research / paper only. No real orders, ever.** No broker connection, no order routing, no
   live trading. `BROKER_ENABLED` / `REAL_ORDER_ENABLED` / `ENABLE_LIVE_TRADING` are FORBIDDEN.
   Every execution path must preserve the "No real order sent." invariant.
2. **Local only.** No cloud APIs, paid services, LLM calls, or HTML scraping. Data and artifacts
   stay on local disk.
3. **Secrets stay in `.env`** (git-ignored). Never commit secrets; update `.env.example` (template).

## Before you change code

- The real CLI is `bist_signal_bot/cli/main.py:run_cli`; `__main__.py` and the `bist-signal-bot`
  script both delegate to it. Don't add a second/mock CLI.
- Configuration flows through `config/settings.py` + `config/defaults.py`
  (`os.environ > .env > .env.example > DEFAULTS > name-based`). Add type-critical keys to
  `config/defaults.py`; never return the `"mock_value"` sentinel.
- Logging: stdlib `logging` via `core/logging_setup.get_logger`.

## Verify your change

```bash
python -m bist_signal_bot version
python -m bist_signal_bot healthcheck
python -m bist_signal_bot bootstrap demo
python -m bist_signal_bot runtime dry-run
.venv/Scripts/python -m pytest bist_signal_bot/tests/<area> -q
```

## Current focus & known gaps

See the "Known gaps / follow-ups" section of [CLAUDE.md](CLAUDE.md): portfolio construction
rebuild, full runtime step coverage (data refresh / regime / ML inference / cleanup), enabling
the ML filter + drift→retrain loop once a baseline model is registered, and migrating
`getattr(settings, X, default)` sites onto `DEFAULTS`.
