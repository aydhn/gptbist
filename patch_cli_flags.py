
import re

with open("bist_signal_bot/cli/parsers.py", "r") as f:
    content = f.read()

# Add --monitoring to healthcheck if not present
if "healthcheck_parser.add_argument('--monitoring'" not in content:
    content = content.replace("healthcheck_parser.add_argument('--json', action='store_true')", "healthcheck_parser.add_argument('--json', action='store_true')\n    healthcheck_parser.add_argument('--monitoring', action='store_true')")

# Add --monitoring to doctor
if "doctor_parser.add_argument('--monitoring'" not in content:
    content = content.replace("doctor_parser.add_argument('--json', action='store_true')", "doctor_parser.add_argument('--json', action='store_true')\n    doctor_parser.add_argument('--monitoring', action='store_true')")

# Add --include-monitoring to qa release-gate
if "qa_release_gate.add_argument('--include-monitoring'" not in content:
    content = content.replace("qa_release_gate.add_argument('--json', action='store_true')", "qa_release_gate.add_argument('--json', action='store_true')\n    qa_release_gate.add_argument('--include-monitoring', action='store_true')")

# Add --include-monitoring to ops readiness
if "ops_readiness.add_argument('--include-monitoring'" not in content:
    content = content.replace("ops_readiness.add_argument('--json', action='store_true')", "ops_readiness.add_argument('--json', action='store_true')\n    ops_readiness.add_argument('--include-monitoring', action='store_true')")

# Add --include-monitoring to reports daily
if "reports_daily.add_argument('--include-monitoring'" not in content:
    content = content.replace("reports_daily.add_argument('--json', action='store_true')", "reports_daily.add_argument('--json', action='store_true')\n    reports_daily.add_argument('--include-monitoring', action='store_true')")

with open("bist_signal_bot/cli/parsers.py", "w") as f:
    f.write(content)
