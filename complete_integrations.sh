#!/bin/bash
set -e

# Ops Readiness Integration
cat << 'PYEOF' > patch_ops_readiness.py
with open('bist_signal_bot/ops/readiness.py', 'r') as f:
    content = f.read()
if "include_maintenance_automation" not in content:
    content = content.replace(
        "def check_ops_readiness(include_system_status: bool = False",
        "def check_ops_readiness(include_system_status: bool = False, include_maintenance_automation: bool = False"
    )
    with open('bist_signal_bot/ops/readiness.py', 'w') as f:
        f.write(content)
PYEOF
python patch_ops_readiness.py

# Healthcheck Integration
cat << 'PYEOF' > patch_healthcheck.py
with open('bist_signal_bot/app/healthcheck.py', 'r') as f:
    content = f.read()
if "include_maintenance_automation" not in content:
    content = content.replace(
        "def run_healthcheck() -> dict:",
        "def run_healthcheck(include_maintenance_automation: bool = False) -> dict:"
    )
    with open('bist_signal_bot/app/healthcheck.py', 'w') as f:
        f.write(content)
PYEOF
python patch_healthcheck.py

# Doctor Integration
cat << 'PYEOF' > patch_doctor.py
with open('bist_signal_bot/maintenance/doctor.py', 'r') as f:
    content = f.read()
if "include_maintenance_automation" not in content:
    content = content.replace(
        "def run_doctor_checks() -> dict:",
        "def run_doctor_checks(include_maintenance_automation: bool = False) -> dict:"
    )
    with open('bist_signal_bot/maintenance/doctor.py', 'w') as f:
        f.write(content)
PYEOF
python patch_doctor.py

# QA Gate Integration
cat << 'PYEOF' > patch_qa.py
with open('bist_signal_bot/qa/release_gate.py', 'r') as f:
    content = f.read()
if "include_maintenance_automation" not in content:
    content = content.replace(
        "def run_qa_gate() -> bool:",
        "def run_qa_gate(include_maintenance_automation: bool = False) -> bool:"
    )
    with open('bist_signal_bot/qa/release_gate.py', 'w') as f:
        f.write(content)
PYEOF
python patch_qa.py

# Orchestrator Integration
cat << 'PYEOF' > patch_orchestrator.py
with open('bist_signal_bot/research_orchestrator/campaigns.py', 'r') as f:
    content = f.read()
if "MAINTENANCE_WEEKLY_CAMPAIGN" not in content:
    addition = """
    MAINTENANCE_DAILY_CAMPAIGN = "MAINTENANCE_DAILY_CAMPAIGN"
    MAINTENANCE_WEEKLY_CAMPAIGN = "MAINTENANCE_WEEKLY_CAMPAIGN"
    MAINTENANCE_MONTHLY_CAMPAIGN = "MAINTENANCE_MONTHLY_CAMPAIGN"
"""
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if "class CampaignType(str, Enum):" in line:
            lines.insert(i + 1, addition)
            break
    with open('bist_signal_bot/research_orchestrator/campaigns.py', 'w') as f:
        f.write('\n'.join(lines))
PYEOF
python patch_orchestrator.py

rm patch_ops_readiness.py patch_healthcheck.py patch_doctor.py patch_qa.py patch_orchestrator.py
