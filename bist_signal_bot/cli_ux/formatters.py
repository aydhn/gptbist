import json
from typing import Any, Dict, List, Optional
from bist_signal_bot.cli_ux.models import CLIOutputEnvelope, CLIOutputMode

class CLIUXFormatter:
    def __init__(self, settings=None):
        self.settings = settings
        # Use existing redaction or fallback
        try:
            from bist_signal_bot.security.redaction import SecretRedactor
            self.redactor = SecretRedactor()
        except ImportError:
            self.redactor = None

    def format_envelope(self, envelope: CLIOutputEnvelope, mode: CLIOutputMode = CLIOutputMode.TEXT) -> str:
        envelope.payload = self.sanitize_payload(envelope.payload)

        if mode == CLIOutputMode.JSON:
            return self.format_json(envelope)
        elif mode == CLIOutputMode.TABLE:
            # Fallback to text if table not specifically formatted
            return self.format_text(envelope)
        elif mode == CLIOutputMode.MARKDOWN:
            return self.format_markdown(envelope)
        elif mode == CLIOutputMode.QUIET:
            return f"{envelope.status.value}"
        elif mode == CLIOutputMode.VERBOSE:
            return self.format_text(envelope) + f"\nMetadata: {envelope.metadata}"
        else:
            return self.format_text(envelope)

    def format_json(self, envelope: CLIOutputEnvelope) -> str:
        envelope.payload = self.sanitize_payload(envelope.payload)
        indent = getattr(self.settings, "CLI_JSON_INDENT", 2) if self.settings else 2
        sort_keys = getattr(self.settings, "CLI_JSON_SORT_KEYS", True) if self.settings else True

        # Convert envelope to dict (using pydantic dict)
        env_dict = envelope.dict()
        # Convert enums
        env_dict['status'] = env_dict['status'].value
        env_dict['output_mode'] = env_dict['output_mode'].value

        # Convert datetime
        if 'created_at' in env_dict and env_dict['created_at']:
             env_dict['created_at'] = env_dict['created_at'].isoformat()

        return json.dumps(env_dict, indent=indent, sort_keys=sort_keys)

    def format_text(self, envelope: CLIOutputEnvelope) -> str:
        lines = [
            f"Status: {envelope.status.value}",
            f"Command: {envelope.command}",
            f"Exit Code: {envelope.exit_code}",
        ]

        if envelope.warnings:
            lines.append("\nWarnings:")
            for w in envelope.warnings:
                lines.append(f"  - {w}")

        if envelope.errors:
            lines.append("\nErrors:")
            for e in envelope.errors:
                lines.append(f"  - {e}")

        lines.append(f"\nPayload:\n{json.dumps(envelope.payload, indent=2)}")

        if envelope.next_steps:
             lines.append("\nNext Steps:")
             for ns in envelope.next_steps:
                 lines.append(f"  - {ns}")

        lines.append(f"\n{envelope.disclaimer}")

        return "\n".join(lines)

    def format_table(self, rows: List[Dict[str, Any]], columns: Optional[List[str]] = None) -> str:
        if not rows:
            return "No data"

        cols = columns if columns else list(rows[0].keys())

        # Simple text table fallback
        table = " | ".join(cols) + "\n"
        table += "-" * len(table) + "\n"

        for row in rows:
            table += " | ".join(str(row.get(c, "")) for c in cols) + "\n"

        return table

    def format_markdown(self, envelope: CLIOutputEnvelope) -> str:
        return f"```json\n{self.format_json(envelope)}\n```"

    def sanitize_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {}
        unsafe_keys = ["token", "secret", "password", "key", "api_key"]

        for k, v in payload.items():
            is_unsafe = any(u in k.lower() for u in unsafe_keys)

            if is_unsafe:
                sanitized[k] = "***REDACTED***"
            elif isinstance(v, dict):
                sanitized[k] = self.sanitize_payload(v)
            elif isinstance(v, list):
                sanitized[k] = [self.sanitize_payload(i) if isinstance(i, dict) else i for i in v]
            else:
                sanitized[k] = v

        if self.redactor:
            # Further redaction if available
            try:
                # Mocked behaviour if redactor supports dictionary redaction directly
                if hasattr(self.redactor, 'redact_dict'):
                    sanitized = self.redactor.redact_dict(sanitized)
            except Exception:
                pass

        return sanitized
