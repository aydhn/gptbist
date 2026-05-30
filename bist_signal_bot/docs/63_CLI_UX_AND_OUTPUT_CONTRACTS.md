# CLI UX and Output Contracts (Phase 91)

## Architecture

The CLI UX layer provides a stable, script-friendly, and safe user experience for the `bist_signal_bot`. It standardizes outputs using rigid JSON schemas, standardizes exit codes, normalizes error messages, and ensures that sensitive data is redacted before output.

## CLIOutputEnvelope

All CLI commands (especially when run with `--json`) wrap their responses in a standard `CLIOutputEnvelope`.

### Fields
- `envelope_id`: Unique identifier for the output event.
- `created_at`: Timestamp (ISO).
- `command`: The command executed.
- `status`: Output status (e.g., `SUCCESS`, `WARNING`, `FAILED`, `BLOCKED`).
- `exit_code`: Numeric exit code representing the result (e.g., 0 for success).
- `output_mode`: Mode requested (`JSON`, `TEXT`, `QUIET`, etc).
- `payload`: The actual command data (must match an expected OutputSchema).
- `warnings`: List of warning messages.
- `errors`: List of error messages.
- `next_steps`: Suggested actionable next steps.
- `disclaimer`: Required statement clarifying this is not investment advice.
- `metadata`: Any extra tracing info.

## Command Contracts

Every command follows a `CLICommandContract` defining its expected stable fields, its associated JSON schema, its risk level, and its specific exit codes. This prevents API drift for consumers wrapping the CLI.

## Exit Codes

Exit codes are standardized:
- `0` (SUCCESS): Operation completed without blocking issues.
- `1` (WARNING): Operation completed but with warnings/partial success.
- `2` (USER_ERROR): Invalid user input.
- `5` (SAFETY_BLOCKED): Prevented due to safety/policy constraint.
- `6` (CONFIRM_REQUIRED): A destructive command was run without `--confirm`.
- `10` (INTERNAL_ERROR): Unexpected error.

## Workflow Runner & Recipe Executor

Workflows define multi-step execution graphs. The `CLIWorkflowRunner` enforces dry-run by default, blocks destructive actions without confirmation, and generates an overarching `WorkflowRun` result artifact.
Recipes map strings like "QUICKSTART" to specific workflows.

## Safety & Security
1. **Redaction:** `CLIUXFormatter` sanitizes all dict payloads, explicitly masking words containing "token", "password", "secret", "key".
2. **Safe Language Guard:** Claims like "trade ready", "buy/sell" are blocked.
3. **No Broker Connection:** The runner mocks and ensures tests/runs operate offline as a local research tool.
