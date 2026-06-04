import re

def fix_changelog():
    path = "bist_signal_bot/release_policy/changelog.py"
    with open(path, "r") as f:
        content = f.read()
    content = content.replace('lines = ["# Changelog\n"]', 'lines = ["# Changelog\\n"]')
    with open(path, "w") as f:
        f.write(content)

def fix_settings():
    path = "bist_signal_bot/config/settings.py"
    with open(path, "r") as f:
        lines = f.readlines()

    # Simple fix: unindent the settings we appended.
    fixed = []
    for line in lines:
        if line.startswith("    ENABLE_RELEASE_POLICY:"):
            line = line.lstrip()
        elif line.startswith("    RELEASE_POLICY_"):
            line = line.lstrip()
        elif line.startswith("    RUNTIME_RELEASE_POLICY_"):
            line = line.lstrip()
        elif line.startswith("    QA_INCLUDE_"):
            line = line.lstrip()
        elif line.startswith("    OPS_INCLUDE_"):
            line = line.lstrip()
        elif line.startswith("    REPORT_INCLUDE_"):
            line = line.lstrip()
        elif line.startswith("    RESEARCH_AUTO_"):
            line = line.lstrip()
        fixed.append(line)

    with open(path, "w") as f:
        f.write("".join(fixed))

if __name__ == "__main__":
    fix_changelog()
    fix_settings()
