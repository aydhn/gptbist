with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# I will find 'def add_security_parser' and truncate everything after it.
# Then I will append the correct 'add_security_parser' and 'add_quality_parser'

parts = content.split("def add_security_parser(subparsers):")
clean_content = parts[0]

security_and_quality = """def add_security_parser(subparsers):
    security_parser = subparsers.add_parser("security", help="Manage security, secret hygiene, and kill-switches.")
    security_subparsers = security_parser.add_subparsers(dest="security_command", required=True)

    audit_parser = security_subparsers.add_parser("audit", help="Run a security configuration audit.")
    audit_parser.add_argument("--json", action="store_true", help="Output as JSON.")
    audit_parser.add_argument("--markdown", action="store_true", help="Output as Markdown.")

    preflight_parser = security_subparsers.add_parser("preflight", help="Run security preflight checks.")
    preflight_parser.add_argument("--runtime", action="store_true", help="Run runtime preflight.")
    preflight_parser.add_argument("--notification", action="store_true", help="Run notification preflight (dummy payload).")
    preflight_parser.add_argument("--json", action="store_true", help="Output as JSON.")

    redact_parser = security_subparsers.add_parser("redact", help="Test secret redaction on text.")
    redact_parser.add_argument("--text", required=True, type=str, help="Text to redact.")
    redact_parser.add_argument("--json", action="store_true", help="Output as JSON.")

    ks_parser = security_subparsers.add_parser("kill-switch", help="Manage operational kill switch.")
    ks_sub = ks_parser.add_subparsers(dest="ks_command", required=True)

    ks_sub.add_parser("status", help="Show kill switch status.")

    activate_parser = ks_sub.add_parser("activate", help="Activate the kill switch.")
    activate_parser.add_argument("--scope", type=str, default="ALL", help="Scope of the kill switch (e.g. ALL, RUNTIME, PAPER).")
    activate_parser.add_argument("--reason", type=str, required=True, help="Reason for activation.")

    deactivate_parser = ks_sub.add_parser("deactivate", help="Deactivate the kill switch.")
    deactivate_parser.add_argument("--confirm", action="store_true", help="Confirm deactivation.")

    scan_parser = security_subparsers.add_parser("scan-source", help="Scan source files for forbidden actions.")
    scan_parser.add_argument("--path", type=str, required=True, help="Path to scan.")
    scan_parser.add_argument("--json", action="store_true", help="Output as JSON.")

    config_parser = security_subparsers.add_parser("config", help="Dump safely redacted config.")
    config_parser.add_argument("--json", action="store_true", help="Output as JSON.")

def add_quality_parser(subparsers):
    quality_parser = subparsers.add_parser("quality", help="Run Quality Gate checks")
    quality_subparsers = quality_parser.add_subparsers(dest="quality_command", required=True)

    run_parser = quality_subparsers.add_parser("run", help="Run the full Quality Gate")
    run_parser.add_argument("--suite", type=str, help="QualitySuite to run (ALL, SMOKE, UNIT, SECURITY, FAST, etc.)")
    run_parser.add_argument("--gate", type=str, help="QualityGateLevel (RELAXED, STANDARD, STRICT, RELEASE)")
    run_parser.add_argument("--coverage", action="store_true", help="Force coverage run")
    run_parser.add_argument("--static", action="store_true", help="Force static analysis run")
    run_parser.add_argument("--type-check", action="store_true", help="Force type checking run")
    run_parser.add_argument("--regression-smoke", action="store_true", help="Force regression smoke test run")
    run_parser.add_argument("--save-report", action="store_true", help="Force saving report")
    run_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    smoke_parser = quality_subparsers.add_parser("smoke", help="Run only smoke checks")
    smoke_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    security_parser = quality_subparsers.add_parser("security", help="Run only security checks")
    security_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    imports_parser = quality_subparsers.add_parser("imports", help="Run only import checks")
    imports_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    coverage_parser = quality_subparsers.add_parser("coverage", help="Run only coverage checks")
    coverage_parser.add_argument("--threshold", type=float, help="Coverage threshold pct")
    coverage_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    regression_parser = quality_subparsers.add_parser("regression", help="Run only regression checks")
    regression_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    recent_parser = quality_subparsers.add_parser("recent", help="List recent quality runs")
    recent_parser.add_argument("--limit", type=int, default=20, help="Max runs to show")
    recent_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")

    config_parser = quality_subparsers.add_parser("config", help="Show quality gate configuration")
    config_parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
"""

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.write(clean_content + security_and_quality)
