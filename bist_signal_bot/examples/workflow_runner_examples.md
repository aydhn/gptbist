# Workflow Runner Examples

## Quickstart

Run a series of commands designed for onboarding, enforcing dry-run by default to ensure safe exploration.

```bash
python -m bist_signal_bot cli-ux workflow run --name quickstart --dry-run
```

Output:
```
Workflow Run: quickstart
Status: SUCCESS
Exit Code: 0
Steps:
  [SUCCESS] python -m bist_signal_bot healthcheck
  [SUCCESS] python -m bist_signal_bot scan symbols
```

## Offline Demo

Run the offline demo recipe using JSON output mode.

```bash
python -m bist_signal_bot cli-ux recipe run OFFLINE_DEMO --save --json
```

Output:
```json
{
  "run_id": "c1f71dae-2ba7-440d-b87f-e221b0660416",
  "created_at": "2024-03-10T12:15:00Z",
  "workflow_name": "Recipe_OFFLINE_DEMO",
  "profile_name": null,
  "status": "SUCCESS",
  "exit_code": 0,
  "steps": [
    {
      "step_id": "step-1",
      "order": 1,
      "command": "python -m bist_signal_bot config show",
      "status": "SUCCESS",
      "exit_code": 0,
      "started_at": "2024-03-10T12:15:00Z",
      "finished_at": "2024-03-10T12:15:00.001Z",
      "elapsed_seconds": 0.001,
      "output_ref": "mocked_output_for_step-1",
      "warnings": [],
      "errors": [],
      "metadata": {}
    },
    {
      "step_id": "step-2",
      "order": 2,
      "command": "python -m bist_signal_bot scan symbols --limit 5",
      "status": "SUCCESS",
      "exit_code": 0,
      "started_at": "2024-03-10T12:15:01Z",
      "finished_at": "2024-03-10T12:15:01.001Z",
      "elapsed_seconds": 0.001,
      "output_ref": "mocked_output_for_step-2",
      "warnings": [],
      "errors": [],
      "metadata": {}
    }
  ],
  "artifacts": {},
  "warnings": [],
  "errors": [],
  "disclaimer": "Workflow run is local research automation only. It is not investment advice or an order instruction. No real order was sent.",
  "metadata": {}
}
```
