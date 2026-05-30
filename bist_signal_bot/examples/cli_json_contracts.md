# CLI JSON Contracts

Here is an example of what the `--json` output looks like when wrapping command results in a `CLIOutputEnvelope`.

## Healthcheck Example
```json
{
  "envelope_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2024-03-10T12:00:00Z",
  "command": "healthcheck",
  "status": "SUCCESS",
  "exit_code": 0,
  "output_mode": "JSON",
  "payload": {
    "status": "pass",
    "version": "1.0.0",
    "components": {
      "portfolio_ledger": {"enabled": true},
      "whatif_lab": {"enabled": true}
    }
  },
  "warnings": [],
  "errors": [],
  "next_steps": [],
  "disclaimer": "CLI output is local research software output only. It is not investment advice or a trading instruction. No real order was sent.",
  "metadata": {}
}
```

## Scanner Example
```json
{
  "envelope_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "created_at": "2024-03-10T12:05:00Z",
  "command": "scan symbols",
  "status": "SUCCESS",
  "exit_code": 0,
  "output_mode": "JSON",
  "payload": {
    "scan_id": "scan-20240310",
    "symbols_scanned": 15,
    "signals_found": 3,
    "top_candidates": ["AKBNK", "GARAN", "KCHOL"]
  },
  "warnings": [],
  "errors": [],
  "next_steps": ["python -m bist_signal_bot review-workflow"],
  "disclaimer": "CLI output is local research software output only. It is not investment advice or a trading instruction. No real order was sent.",
  "metadata": {}
}
```
