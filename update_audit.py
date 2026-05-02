import re

with open("bist_signal_bot/core/audit.py", "r") as f:
    content = f.read()

# Add PATTERN_FEATURE_CALCULATION to AuditEventType
if "PATTERN_FEATURE_CALCULATION" not in content:
    insertion_point = content.find("VOLUME_FEATURE_CALCULATION = \"VOLUME_FEATURE_CALCULATION\"")
    if insertion_point != -1:
        end_of_line = content.find("\n", insertion_point)
        content = content[:end_of_line] + "\n    PATTERN_FEATURE_CALCULATION = \"PATTERN_FEATURE_CALCULATION\"" + content[end_of_line:]
    else:
        print("Could not find insertion point for AuditEventType")

with open("bist_signal_bot/core/audit.py", "w") as f:
    f.write(content)
