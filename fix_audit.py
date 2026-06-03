def fix_audit():
    path = "bist_signal_bot/core/audit.py"
    with open(path, "r") as f:
        lines = f.readlines()

    fixed = []
    for line in lines:
        if line.startswith('    RELEASE_BRANCH_') or line.startswith('    VERSION_SNAPSHOT_') or line.startswith('    COMPATIBILITY_') or line.startswith('    CHANGE_') or line.startswith('    CHANGELOG_') or line.startswith('    MIGRATION_') or line.startswith('    DEPRECATION_') or line.startswith('    FINAL_CLOSURE_') or line.startswith('    RELEASE_POLICY_'):
            line = line.lstrip()
        fixed.append(line)

    with open(path, "w") as f:
        f.writelines(fixed)

if __name__ == "__main__":
    fix_audit()
