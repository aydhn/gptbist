with open("bist_signal_bot/core/audit.py", "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "class AuditEventType(Enum):" in line:
        new_lines.append(line)
        new_lines.append("    QUALITY_RUN_STARTED = \"QUALITY_RUN_STARTED\"\n")
        new_lines.append("    QUALITY_RUN_COMPLETED = \"QUALITY_RUN_COMPLETED\"\n")
        new_lines.append("    QUALITY_RUN_FAILED = \"QUALITY_RUN_FAILED\"\n")
        new_lines.append("    QUALITY_CHECK_COMPLETED = \"QUALITY_CHECK_COMPLETED\"\n")
        new_lines.append("    QUALITY_GATE_FAILED = \"QUALITY_GATE_FAILED\"\n")
        new_lines.append("    QUALITY_REPORT_SAVED = \"QUALITY_REPORT_SAVED\"\n")
        new_lines.append("    QUALITY_REGRESSION_SMOKE_RUN = \"QUALITY_REGRESSION_SMOKE_RUN\"\n")
        new_lines.append("    QUALITY_SECURITY_CHECK_RUN = \"QUALITY_SECURITY_CHECK_RUN\"\n")
    elif "QUALITY_RUN_STARTED" not in line and "QUALITY_RUN_COMPLETED" not in line and "QUALITY_RUN_FAILED" not in line and "QUALITY_CHECK_COMPLETED" not in line and "QUALITY_GATE_FAILED" not in line and "QUALITY_REPORT_SAVED" not in line and "QUALITY_REGRESSION_SMOKE_RUN" not in line and "QUALITY_SECURITY_CHECK_RUN" not in line:
        new_lines.append(line)

with open("bist_signal_bot/core/audit.py", "w") as f:
    f.writelines(new_lines)
